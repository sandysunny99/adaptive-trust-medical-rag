"""Image-text grounding through the real routes and pipeline (upload -> SSE -> confirm).

Reproduces the 2026-10-22 browser finding: the vision model returned "Acetaminophen" with HIGH confidence
(and its own transcription naming it) for a blank white image. Vision, OCR, the RxNorm normaliser and
retrieval are deterministic stubs that count their calls; no real model or patient data is used.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
from types import SimpleNamespace

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from adaptive_trust_medical_rag.api.app import app
from adaptive_trust_medical_rag.llm_backend.vision_interfaces import (
    ExtractionConfidence,
    ExtractionResult,
    MedicationCandidate,
)
from adaptive_trust_medical_rag.services.image_grounding import OCR_ERROR, OCR_UNAVAILABLE, ImageText

HIGH = ExtractionConfidence.HIGH
ACETAMINOPHEN = MedicationCandidate(raw_text="Acetaminophen", normalized_text="acetaminophen", confidence=HIGH)
WARFARIN = MedicationCandidate(raw_text="Warfarin 5mg", normalized_text="warfarin", confidence=HIGH)


class Vision:
    def __init__(self, candidates, transcription="", provider="stub_vision"):
        self.provider_name, self.model_name = provider, "stub-model"
        self.candidates, self.transcription, self.provider, self.calls = candidates, transcription, provider, 0

    async def extract_medications(self, image_bytes, mime_type):
        self.calls += 1
        return ExtractionResult(raw_text=self.transcription, warnings=[], candidate_medications=list(self.candidates),
                                provider_used=self.provider, model_used="stub-model")


class Counting:
    def __init__(self):
        self.calls = 0

    async def normalize_batch(self, names):
        self.calls += 1
        return [SimpleNamespace(raw_text=n, generic_name=n.lower(), rxcui={"warfarin": "11289"}.get(n.lower()),
                                brand_name=None, formulation=None, confidence=1.0, source="TEST") for n in names]

    def retrieve(self, query, query_drugs, top_k=20):
        self.calls += 1
        return []


@pytest.fixture
def stubs(monkeypatch):
    s = SimpleNamespace(normalizer=Counting(), retrieval=Counting())
    for name, value in (("drug_normalizer", s.normalizer), ("retrieval_engine", s.retrieval),
                        ("claim_verifier", object()), ("llm_backend", object()), ("verified_source_links", {})):
        monkeypatch.setattr(app.state, name, value, raising=False)

    def use(vision, ocr):
        monkeypatch.setattr(app.state, "vision_backend", vision, raising=False)
        monkeypatch.setattr(app.state, "image_text_recognizer", ocr, raising=False)
    s.use = use
    return s


def blank_png():
    buf = io.BytesIO()
    Image.new("RGB", (400, 300), "white").save(buf, format="PNG")
    return buf.getvalue()


def events_of(text):
    out, current = [], {}
    for line in text.splitlines():
        if line.startswith("event: "):
            current["event"] = line[7:]
        elif line.startswith("data: "):
            current["data"] = json.loads(line[6:])
        elif not line and current:
            out.append(current)
            current = {}
    return out + ([current] if current else [])


async def upload_and_stream(confirm=None, png=None):
    """Upload, read the stream; confirm once the request waits, if a payload is given. -> (events, request_id)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"image": ("rx.png", png or blank_png(), "image/png")}
        request_id = (await client.post("/api/v1/analyze/prescription", files=files)).json()["request_id"]
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{request_id}"))
        if confirm is not None:
            while not (app.state.pending_analyses.get(request_id) or {}).get("awaiting_confirmation"):
                assert not stream.done(), "the request never waited for a confirmation"
                await asyncio.sleep(0.01)
            assert (await client.post(f"/api/v1/analyze/{request_id}/confirm", json=confirm)).status_code == 200
        # Generous: the first request of a process also loads the models (_lazy_init_models).
        return events_of((await asyncio.wait_for(stream, timeout=180)).text), request_id


def names(events, kind):
    return [e.get("data", {}) for e in events if e.get("event") == kind]


# ── The blank-image hallucination ─────────────────────────────────────────────

def test_a_blank_image_never_reaches_the_vision_model(stubs, ocr_reads):
    vision = Vision([ACETAMINOPHEN], transcription="Acetaminophen 500 mg")
    stubs.use(vision, ocr_reads())  # the independent OCR reads nothing on a blank page
    events, _ = asyncio.run(upload_and_stream())
    (error,) = names(events, "error")
    assert (error["code"], error["suggested"]) == ("NO_VERIFIED_MEDICATIONS", 0)
    assert vision.calls == 0 and (stubs.normalizer.calls, stubs.retrieval.calls) == (0, 0)


@pytest.mark.parametrize("provider", ["nvidia_vision", "groq_vision_fallback"])
def test_a_high_confidence_hallucination_absent_from_the_image_text_is_withheld(stubs, ocr_reads, provider):
    # The image has text, but no drug name. The model's own transcription names the drug too: it is the
    # same response, so it proves nothing.
    vision = Vision([ACETAMINOPHEN], transcription="Acetaminophen 500 mg", provider=provider)
    stubs.use(vision, ocr_reads("SYNTHETIC TEST PRESCRIPTION"))
    events, request_id = asyncio.run(upload_and_stream())
    (error,) = names(events, "error")
    assert error["code"] == "NO_VERIFIED_MEDICATIONS" and error["suggested"] == 1
    assert not names(events, "medication_candidates_extracted") and not names(events, "confirmation_required")
    assert "Acetaminophen" not in json.dumps(events)
    assert (stubs.normalizer.calls, stubs.retrieval.calls) == (0, 0)  # no RxNorm, no evidence retrieval
    assert vision.calls == 1


def test_no_candidates_and_no_text_ends_without_a_confirmation_wait(stubs, ocr_reads):
    stubs.use(Vision([]), ocr_reads())
    events, _ = asyncio.run(upload_and_stream())
    assert names(events, "error")[0]["code"] == "NO_VERIFIED_MEDICATIONS"
    assert not names(events, "confirmation_required") and stubs.normalizer.calls == 0


@pytest.mark.parametrize("status", [OCR_UNAVAILABLE, OCR_ERROR])
def test_an_ocr_failure_is_reported_apart_from_an_image_without_medications(stubs, status):
    stubs.use(Vision([WARFARIN], transcription="Warfarin 5mg"), lambda b, m: ImageText(status, reason="test"))
    events, _ = asyncio.run(upload_and_stream())
    (error,) = names(events, "error")
    assert (error["code"], error["ocr_status"]) == ("IMAGE_TEXT_UNVERIFIABLE", status)
    assert not names(events, "confirmation_required") and stubs.normalizer.calls == 0


# ── Supported candidates still reach the user, who must confirm ───────────────

def test_only_the_candidate_in_the_image_text_is_shown_and_the_analysis_waits_for_the_user(stubs, ocr_reads):
    stubs.use(Vision([WARFARIN, ACETAMINOPHEN]), ocr_reads("SYNTHETIC RX", "Warfarin 5mg tablet once daily"))
    confirm = {"confirmed_medications": [
        {"name": "Warfarin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Warfarin 5mg"}]}
    events, _ = asyncio.run(upload_and_stream(confirm))
    (extracted,) = names(events, "medication_candidates_extracted")
    # The evidence is the name the user confirms ("warfarin"), as printed in the image.
    assert [(c["raw_text"], c["image_text_evidence"]) for c in extracted["candidates"]] == [
        ("Warfarin 5mg", "Warfarin")]
    assert extracted["warnings"] == ["1 suggested name(s) did not appear in the image text and were left out."]
    assert "Acetaminophen" not in json.dumps(events)
    assert names(events, "confirmation_required") and stubs.normalizer.calls == 1  # ran once, after confirmation


def test_a_name_never_shown_cannot_be_confirmed_as_taken_from_the_image(stubs, ocr_reads):
    stubs.use(Vision([WARFARIN, ACETAMINOPHEN]), ocr_reads("Warfarin 5mg"))
    confirm = {"confirmed_medications": [
        {"name": "Warfarin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Warfarin 5mg"},
        {"name": "Warfarin sodium", "status": "EDITED", "source": "USER_EDITED", "raw_detected_name": "Warfarin 5mg"},
        {"name": "Acetaminophen", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Acetaminophen"},
        {"name": "Aspirin", "status": "EDITED", "source": "USER_EDITED", "raw_detected_name": "Acetaminophen"},
        {"name": "Metformin", "status": "USER_ADDED", "source": "USER", "raw_detected_name": None}]}
    events, _ = asyncio.run(upload_and_stream(confirm))
    (rxnorm,) = names(events, "rxnorm")
    provenance = {m["raw_text"]: (m["confirmation_status"], m["source"]) for m in rxnorm["entities"]}
    assert provenance == {"Warfarin": ("CONFIRMED", "VISION"),                 # shown, confirmed
                          "Warfarin sodium": ("EDITED", "USER_EDITED"),        # a shown candidate, corrected
                          "Acetaminophen": ("USER_ADDED", "USER"),             # never shown
                          "Aspirin": ("USER_ADDED", "USER"),                   # "edited" from a name never shown
                          "Metformin": ("USER_ADDED", "USER")}                 # added by hand


# ── Privacy: the image is read here first; it leaves only if text was found ──

def _raising(image_bytes, mime):
    raise RuntimeError("OCR crashed")


@pytest.mark.parametrize("ocr, code, status", [
    (lambda b, m: ImageText(OCR_UNAVAILABLE, reason="no local OCR engine"), "IMAGE_TEXT_UNVERIFIABLE", OCR_UNAVAILABLE),
    (lambda b, m: ImageText(OCR_ERROR, reason="TimeoutExpired"), "IMAGE_TEXT_UNVERIFIABLE", OCR_ERROR),
    (_raising, "IMAGE_TEXT_UNVERIFIABLE", OCR_ERROR),
    (lambda b, m: ImageText("OK", "", "fixture-ocr"), "NO_VERIFIED_MEDICATIONS", None),
    (lambda b, m: ImageText("OK", "  \r\n ", "fixture-ocr"), "NO_VERIFIED_MEDICATIONS", None),
], ids=["unavailable", "timeout", "exception", "empty", "blank-lines"])
def test_no_image_reaches_a_vision_provider_unless_this_server_read_text_in_it(stubs, ocr, code, status):
    vision = Vision([ACETAMINOPHEN], transcription="Acetaminophen 500 mg")
    stubs.use(vision, ocr)
    events, _ = asyncio.run(upload_and_stream())
    assert vision.calls == 0  # the image never left this server
    (error,) = names(events, "error")
    assert error["code"] == code and error.get("ocr_status") == status
    assert not names(events, "confirmation_required") and stubs.normalizer.calls == 0


def test_with_text_found_the_vision_provider_is_called_once_and_its_answer_is_still_checked(stubs, ocr_reads):
    vision = Vision([WARFARIN, ACETAMINOPHEN])
    stubs.use(vision, ocr_reads("Warfarin 5mg tablet"))
    events, _ = asyncio.run(upload_and_stream(
        {"confirmed_medications": [{"name": "Warfarin", "status": "CONFIRMED", "source": "VISION"}]}))
    assert vision.calls == 1
    (extracted,) = names(events, "medication_candidates_extracted")
    assert [c["normalized_text"] for c in extracted["candidates"]] == ["warfarin"]


def test_the_ocr_runs_once_per_image(stubs):
    calls = []

    def counting(image_bytes, mime):
        calls.append(len(image_bytes))
        return ImageText("OK", "Warfarin 5mg", "fixture-ocr")
    stubs.use(Vision([WARFARIN]), counting)
    asyncio.run(upload_and_stream({"confirmed_medications": [
        {"name": "Warfarin", "status": "CONFIRMED", "source": "VISION"}]}))
    assert len(calls) == 1


def test_typed_medication_names_are_analysed_without_the_ocr_or_a_vision_provider(stubs):
    ocr_calls, vision = [], Vision([WARFARIN])
    stubs.use(vision, lambda b, m: ocr_calls.append(1))

    async def analyse_typed_names():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            accepted = await client.post("/api/v1/analyze", json={"drug_names": ["Warfarin", "Aspirin"]})
            return events_of((await client.get(f"/api/v1/stream/{accepted.json()['request_id']}")).text)
    events = asyncio.run(analyse_typed_names())
    assert (ocr_calls, vision.calls) == ([], 0)  # manual entry still works where this server has no OCR
    assert stubs.normalizer.calls >= 1 and not names(events, "medication_candidates_extracted")


# ── OCR failures, platforms, stale text and the real provider chain ──────────

def test_an_ocr_exception_is_an_ocr_failure_and_its_text_is_not_shown(stubs):
    def broken(image_bytes, mime):
        raise RuntimeError(r"cannot open C:\Users\someone\AppData\Local\Temp\tmpabc\upload.png")
    stubs.use(Vision([WARFARIN], transcription="Warfarin 5mg"), broken)
    events, _ = asyncio.run(upload_and_stream())
    (error,) = names(events, "error")
    assert (error["code"], error["ocr_status"]) == ("IMAGE_TEXT_UNVERIFIABLE", "ERROR")
    assert "tmpabc" not in json.dumps(events) and "RuntimeError" not in json.dumps(events)


def test_an_unsupported_platform_tells_the_user_to_enter_names_manually(stubs):
    stubs.use(Vision([WARFARIN]), lambda b, m: ImageText(OCR_UNAVAILABLE, reason="no local OCR engine on this platform"))
    events, _ = asyncio.run(upload_and_stream())
    (error,) = names(events, "error")
    assert error["code"] == "IMAGE_TEXT_UNVERIFIABLE" and error["ocr_status"] == OCR_UNAVAILABLE
    assert "not available on this server" in error["message"] and "enter the medication names" in error["message"]
    assert "Try the upload again" not in error["message"]  # retrying cannot help here


def png_with(lines):
    img = Image.new("RGB", (400, 60 + 40 * len(lines)), "white")
    for i, _ in enumerate(lines):  # distinct bytes per image; the OCR stub decides what each one "reads"
        img.putpixel((i, 0), (0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_the_text_of_an_earlier_image_never_grounds_a_later_request(stubs):
    first, second = png_with(["Warfarin 5mg"]), blank_png()
    reads = {first: "Warfarin 5mg tablet"}  # the second (blank) image reads nothing
    stubs.use(Vision([WARFARIN]), lambda b, m: ImageText("OK", reads.get(b, ""), "fixture-ocr"))
    confirm = {"confirmed_medications": [
        {"name": "Warfarin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Warfarin 5mg"}]}
    events_1, id_1 = asyncio.run(upload_and_stream(confirm, png=first))
    events_2, id_2 = asyncio.run(upload_and_stream(png=second))
    assert id_1 != id_2 and names(events_1, "medication_candidates_extracted")
    assert names(events_2, "error")[0]["code"] == "NO_VERIFIED_MEDICATIONS"
    assert not names(events_2, "medication_candidates_extracted")


HALLUCINATION = {"choices": [{"message": {"content": json.dumps({
    "raw_text": "Acetaminophen 500 mg", "warnings": [],
    "candidate_medications": [{"raw_text": "Acetaminophen", "normalized_text": "acetaminophen",
                               "confidence": "HIGH"}]})}}]}


class _Resp:
    def __init__(self, status, body=None):
        self.status_code, self._body, self.text = status, body, ""

    def json(self):
        return self._body


@pytest.mark.parametrize("groq_reply, code", [(_Resp(200, HALLUCINATION), "NO_VERIFIED_MEDICATIONS"),
                                              (httpx.ReadTimeout("groq"), "VISION_EXTRACTION_ERROR")])
def test_the_real_nvidia_to_groq_chain_gets_the_same_check(stubs, ocr_reads, monkeypatch, groq_reply, code):
    from adaptive_trust_medical_rag.llm_backend.openai_vision_backend import OpenAIVisionBackend
    groq = OpenAIVisionBackend(base_url="https://groq.invalid/v1", api_key="FAKE_TEST_KEY_0001",
                               model_name="groq-vision", provider_name="groq_vision", timeout_s=5.0)
    chain = OpenAIVisionBackend(base_url="https://nvidia.invalid/v1", api_key="FAKE_TEST_KEY_0000",
                                model_name="nvidia-vision", timeout_s=5.0, fallback_backend=groq)
    calls, real_post = [], httpx.AsyncClient.post

    async def post(self, url, *args, **kwargs):
        if ".invalid" not in str(url):  # the test client's own requests to the app
            return await real_post(self, url, *args, **kwargs)
        calls.append(kwargs["json"]["model"])
        reply = httpx.ReadTimeout("nvidia") if len(calls) == 1 else groq_reply
        if isinstance(reply, Exception):
            raise reply
        return reply
    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    stubs.use(chain, ocr_reads("SYNTHETIC TEST PRESCRIPTION"))  # text, but no drug name
    events, _ = asyncio.run(upload_and_stream())
    assert calls == ["nvidia-vision", "groq-vision"]  # one NVIDIA attempt, then Groq
    assert names(events, "error")[0]["code"] == code
    assert not names(events, "medication_candidates_extracted") and stubs.normalizer.calls == 0
    assert "Acetaminophen" not in json.dumps(events)


def test_logs_hold_counts_but_no_names_or_image_text(stubs, ocr_reads, caplog):
    stubs.use(Vision([WARFARIN, ACETAMINOPHEN]), ocr_reads("Patient copy - Warfarin 5mg"))
    with caplog.at_level(logging.DEBUG, logger="adaptive_trust_medical_rag"):
        asyncio.run(upload_and_stream({"confirmed_medications": [
            {"name": "Warfarin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Warfarin 5mg"}]}))
    grounding = [r.getMessage() for r in caplog.records if "found in the image text" in r.getMessage()]
    assert grounding and "2 suggested, 1 found in the image text" in grounding[0]
    assert any("OCR OK, 27 character(s)" in r.getMessage() for r in caplog.records)  # a size, never the text
    assert "Acetaminophen" not in caplog.text and "Patient copy" not in caplog.text
