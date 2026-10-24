"""The confirmation state machine through the real routes and pipeline.

Upload -> extraction -> awaiting confirmation -> exactly one accepted confirmation -> one analysis.
Only unrelated, expensive work is stubbed: the vision provider, the RxNorm normaliser and retrieval
(empty, so a confirmed run ends in an evidence abstention). Each stub counts its calls, so every test
asserts how many times the analysis really ran, not only what the API answered.
"""

from __future__ import annotations

import asyncio
import gc
import io
import json
import logging
import os
import re
import threading
import time
from types import SimpleNamespace

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from adaptive_trust_medical_rag.api.app import app
from adaptive_trust_medical_rag.api.routes import analyze as analyze_routes
from adaptive_trust_medical_rag.llm_backend.interfaces import ModelExecutionError
from adaptive_trust_medical_rag.llm_backend.vision_interfaces import (
    ExtractionConfidence,
    ExtractionResult,
    MedicationCandidate,
)
from adaptive_trust_medical_rag.llm_routing.types import FailureClass
from adaptive_trust_medical_rag.services import image_grounding, live_application
from adaptive_trust_medical_rag.services.image_grounding import OCR_OK, ImageText

REAL_RECOGNIZER = image_grounding.recognize_image_text  # bound before conftest replaces it per test

RXCUI = {"warfarin": "11289", "aspirin": "1191", "ibuprofen": "5640"}
WARFARIN = {"name": "Warfarin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Warfarin 5mg"}
ASPIRIN = {"name": "Aspirin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Aspirin 81mg"}
BOTH = {"confirmed_medications": [WARFARIN, ASPIRIN]}
ONLY_WARFARIN = {"confirmed_medications": [WARFARIN]}


class Vision:
    provider_name, model_name = "stub_vision", "stub-model"

    def __init__(self, fail=False):
        self.fail, self.calls = fail, 0

    async def extract_medications(self, image_bytes, mime_type):
        self.calls += 1
        if self.fail:
            err = ModelExecutionError("Vision Provider Timeout", status_code="TIMEOUT")
            err.failure_class = FailureClass.TIMEOUT
            raise err
        return ExtractionResult(raw_text="SYNTHETIC", warnings=[], candidate_medications=[
            MedicationCandidate(raw_text="Warfarin 5mg", normalized_text="warfarin", confidence=ExtractionConfidence.HIGH),
            MedicationCandidate(raw_text="Aspirin 81mg", normalized_text="aspirin", confidence=ExtractionConfidence.HIGH)])


class Normalizer:
    """Counts analyses: the pipeline normalises the confirmed names once per run."""

    def __init__(self, fail=False):
        self.fail, self.calls, self.seen = fail, 0, []

    async def normalize_batch(self, names):
        self.calls += 1
        self.seen.append(list(names))
        if self.fail:
            raise RuntimeError("normaliser down")
        return [SimpleNamespace(raw_text=n, generic_name=n.lower(), rxcui=RXCUI.get(n.lower()), brand_name=None,
                                formulation=None, confidence=1.0, source="TEST") for n in names]


class NoEvidence:
    def __init__(self):
        self.calls = 0

    def retrieve(self, query, query_drugs, top_k=20):
        self.calls += 1
        return []


@pytest.fixture
def stubs(monkeypatch, ocr_reads):
    # The synthetic prescription image reads the lines the stub vision reports.
    monkeypatch.setattr(app.state, "image_text_recognizer", ocr_reads("Warfarin 5mg", "Aspirin 81mg"), raising=False)
    keep = {k: getattr(app.state, k, None) for k in ("vision_backend", "drug_normalizer", "retrieval_engine",
                                                    "claim_verifier", "llm_backend", "verified_source_links")}
    s = SimpleNamespace(vision=Vision(), normalizer=Normalizer(), retrieval=NoEvidence())
    app.state.vision_backend, app.state.drug_normalizer = s.vision, s.normalizer
    app.state.retrieval_engine, app.state.claim_verifier = s.retrieval, object()
    app.state.llm_backend, app.state.verified_source_links = object(), {}
    yield s
    for k, v in keep.items():
        setattr(app.state, k, v)


def image() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), "white").save(buf, format="PNG")
    return buf.getvalue()


def events_of(text: str) -> list[dict]:
    out, current = [], {}
    for line in text.splitlines():
        if line.startswith("event: "):
            current["event"] = line[7:]
        elif line.startswith("data: "):
            current["data"] = json.loads(line[6:])
        elif not line and current:
            out.append(current)
            current = {}
    return out


async def upload(client) -> str:
    r = await client.post("/api/v1/analyze/prescription", files={"image": ("rx.png", image(), "image/png")})
    assert r.status_code == 200
    return r.json()["request_id"]


async def awaiting(rid: str, stream: asyncio.Task) -> None:
    for _ in range(500):
        if (app.state.pending_analyses.get(rid) or {}).get("awaiting_confirmation") or stream.done():
            return
        await asyncio.sleep(0.01)


def run(flow):
    async def wrapped():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            return await flow(client)
    return asyncio.run(wrapped())


def test_one_valid_confirmation_runs_the_analysis_once(stubs):
    async def flow(client):
        rid = await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{rid}"))
        await awaiting(rid, stream)
        confirm = await client.post(f"/api/v1/analyze/{rid}/confirm", json=BOTH)
        return confirm, events_of((await stream).text)

    confirm, events = run(flow)
    assert (confirm.status_code, confirm.json()["status"]) == (200, "success")
    assert stubs.normalizer.calls == 1 and stubs.normalizer.seen == [["Warfarin", "Aspirin"]]
    assert [e["event"] for e in events].count("rxnorm") == 1
    assert events[-1]["event"] == "abstention"  # no evidence: a safe stop, not a successful analysis


@pytest.mark.parametrize("second", [BOTH, ONLY_WARFARIN], ids=["identical", "conflicting"])
def test_two_simultaneous_confirmations_start_one_analysis(stubs, second):
    async def flow(client):
        rid = await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{rid}"))
        await awaiting(rid, stream)
        a, b = await asyncio.gather(client.post(f"/api/v1/analyze/{rid}/confirm", json=BOTH),
                                    client.post(f"/api/v1/analyze/{rid}/confirm", json=second))
        return a, b, events_of((await stream).text)

    a, b, events = run(flow)
    answers = sorted([(a.status_code, a.json().get("status")), (b.status_code, b.json().get("status"))],
                     key=str)
    if second is BOTH:
        assert answers == [(200, "already_confirmed"), (200, "success")]
    else:
        assert sorted(r.status_code for r in (a, b)) == [200, 409]
    assert stubs.normalizer.calls == 1  # one analysis, whatever arrived second
    accepted = stubs.normalizer.seen[0]
    winner = a if a.status_code == 200 and a.json()["status"] == "success" else b
    assert accepted == [m["name"] for m in winner.json()["confirmed"]]  # the run used the accepted decision
    assert [e["event"] for e in events].count("rxnorm") == 1


def test_a_confirmation_before_extraction_finishes_is_refused_and_starts_nothing(stubs):
    async def flow(client):
        rid = await upload(client)
        early = await client.post(f"/api/v1/analyze/{rid}/confirm", json=BOTH)  # stream not even open
        stream = await client.get(f"/api/v1/stream/{rid}")  # nobody confirms: it times out (2 s in tests)
        return early, events_of(stream.text)

    early, events = run(flow)
    assert early.status_code == 409
    assert stubs.normalizer.calls == 0
    assert events[-1]["event"] == "error" and events[-1]["data"]["code"] == "CONFIRMATION_TIMEOUT"


def test_after_a_failed_extraction_no_confirmation_is_accepted(stubs):
    stubs.vision.fail = True

    async def flow(client):
        rid = await upload(client)
        stream = await client.get(f"/api/v1/stream/{rid}")
        late = await client.post(f"/api/v1/analyze/{rid}/confirm", json=BOTH)
        return late, events_of(stream.text)

    late, events = run(flow)
    assert events[-1]["data"]["code"] == "VISION_EXTRACTION_ERROR"
    assert "confirmation_required" not in [e["event"] for e in events]
    assert late.status_code == 404 and stubs.normalizer.calls == 0


def test_a_finished_request_and_an_old_request_cannot_restart_or_touch_a_newer_one(stubs):
    async def flow(client):
        old = await upload(client)
        s_old = asyncio.create_task(client.get(f"/api/v1/stream/{old}"))
        await awaiting(old, s_old)
        assert (await client.post(f"/api/v1/analyze/{old}/confirm", json=BOTH)).status_code == 200
        await s_old  # the old analysis has finished
        new = await upload(client)
        s_new = asyncio.create_task(client.get(f"/api/v1/stream/{new}"))
        await awaiting(new, s_new)
        replay = await client.post(f"/api/v1/analyze/{old}/confirm", json=ONLY_WARFARIN)
        untouched = "confirmed_medications" not in app.state.pending_analyses[new]
        confirm_new = await client.post(f"/api/v1/analyze/{new}/confirm", json=ONLY_WARFARIN)
        return replay, untouched, confirm_new, events_of((await s_new).text)

    replay, untouched, confirm_new, events = run(flow)
    assert replay.status_code == 404 and untouched
    assert confirm_new.status_code == 200
    assert stubs.normalizer.seen == [["Warfarin", "Aspirin"], ["Warfarin"]]  # one run each, own lists


def test_a_pipeline_error_after_confirmation_counts_as_one_confirmed_run(stubs):
    stubs.normalizer.fail = True

    async def flow(client):
        rid = await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{rid}"))
        await awaiting(rid, stream)
        first = await client.post(f"/api/v1/analyze/{rid}/confirm", json=BOTH)
        events = events_of((await stream).text)
        again = await client.post(f"/api/v1/analyze/{rid}/confirm", json=BOTH)
        return first, events, again

    first, events, again = run(flow)
    assert first.status_code == 200
    assert (events[-1]["event"], events[-1]["data"]["code"]) == ("error", "NORMALIZATION_ERROR")
    # The failed stage arrives before the terminal error, which the client closes the stream on.
    assert events[-2]["data"] == {**events[-2]["data"], "stage": "normalizing", "status": "failed"}
    assert again.status_code == 404  # the failed run is over; a retry is a new upload
    assert stubs.normalizer.calls == 1


# ── Abandoning a request: POST /analyze/{id}/cancel ───────────────────────────

def test_a_cancel_while_awaiting_confirmation_ends_the_request_at_once_and_analyses_nothing(stubs):
    async def flow(client):
        rid = await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{rid}"))
        await awaiting(rid, stream)
        loop = asyncio.get_running_loop()
        t0 = loop.time()
        cancel = await client.post(f"/api/v1/analyze/{rid}/cancel")
        events = events_of((await asyncio.wait_for(stream, 10)).text)
        elapsed = loop.time() - t0
        late_confirm = await client.post(f"/api/v1/analyze/{rid}/confirm", json=BOTH)
        late_cancel = await client.post(f"/api/v1/analyze/{rid}/cancel")
        return cancel, events, elapsed, late_confirm, late_cancel

    cancel, events, elapsed, late_confirm, late_cancel = run(flow)
    assert (cancel.status_code, cancel.json()["status"]) == (200, "cancelled")
    assert (events[-1]["event"], events[-1]["data"]["code"]) == ("error", "ANALYSIS_CANCELLED")
    assert elapsed < 1.5  # released by the cancel, not by the (2 s, under TESTING) confirmation timeout
    assert not any(e["event"] in ("rxnorm", "trust", "answer", "abstention") for e in events)
    assert stubs.normalizer.calls == 0  # no RxNorm, nothing after it
    assert late_confirm.status_code == 404 and late_cancel.status_code == 404  # over: nothing to change


def test_cancelling_twice_is_harmless_and_ends_the_request_once(stubs):
    async def flow(client):
        rid = await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{rid}"))
        await awaiting(rid, stream)
        first, second = await asyncio.gather(client.post(f"/api/v1/analyze/{rid}/cancel"),
                                             client.post(f"/api/v1/analyze/{rid}/cancel"))
        return first, second, events_of((await stream).text)

    first, second, events = run(flow)
    assert {first.status_code, second.status_code} == {200} and second.json()["status"] == "cancelled"
    assert [e["data"].get("code") for e in events if e["event"] == "error"] == ["ANALYSIS_CANCELLED"]
    assert stubs.normalizer.calls == 0


def test_a_cancel_before_the_stream_opens_drops_the_request_and_its_image(stubs):
    async def flow(client):
        rid = await upload(client)
        cancel = await client.post(f"/api/v1/analyze/{rid}/cancel")
        held = rid in app.state.pending_analyses
        stream = await client.get(f"/api/v1/stream/{rid}")
        return cancel, held, events_of(stream.text)

    cancel, held, events = run(flow)
    assert cancel.status_code == 200 and not held  # nothing, image included, is kept
    assert events[-1]["data"]["code"] == "NOT_FOUND" and stubs.vision.calls == 0


def test_a_cancel_during_extraction_abandons_the_provider_call_at_once(stubs, monkeypatch):
    started, abandoned = asyncio.Event(), []

    class SlowVision(Vision):
        async def extract_medications(self, image_bytes, mime_type):
            started.set()
            try:
                await asyncio.sleep(60)  # a provider that has not answered yet
            except asyncio.CancelledError:
                abandoned.append(True)
                raise
    monkeypatch.setattr(app.state, "vision_backend", SlowVision())

    async def flow(client):
        rid = await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{rid}"))
        await asyncio.wait_for(started.wait(), 180)  # the first request of a process also loads the models
        loop = asyncio.get_running_loop()
        t0 = loop.time()
        cancel = await client.post(f"/api/v1/analyze/{rid}/cancel")
        events = events_of((await asyncio.wait_for(stream, 10)).text)
        return cancel, events, loop.time() - t0

    cancel, events, elapsed = run(flow)
    assert cancel.status_code == 200 and elapsed < 1.5  # not after the provider's answer or timeout
    assert (events[-1]["event"], events[-1]["data"]["code"]) == ("error", "ANALYSIS_CANCELLED")
    assert not any(e["event"] in ("medication_candidates_extracted", "confirmation_required") for e in events)
    assert abandoned == [True] and stubs.normalizer.calls == 0


@pytest.mark.parametrize("cancel_during", ["nvidia-vision", "groq-vision"])
def test_a_cancel_during_a_provider_request_interrupts_it_and_starts_no_other(stubs, monkeypatch, cancel_during):
    """The real vision chain and httpx client; only the network send of httpx's transport is replaced."""
    from adaptive_trust_medical_rag.llm_backend.openai_vision_backend import OpenAIVisionBackend
    groq = OpenAIVisionBackend(base_url="https://groq.invalid/v1", api_key="FAKE_TEST_KEY_0001",
                               model_name="groq-vision", provider_name="groq_vision", timeout_s=30.0)
    monkeypatch.setattr(app.state, "vision_backend", OpenAIVisionBackend(
        base_url="https://nvidia.invalid/v1", api_key="FAKE_TEST_KEY_0000", model_name="nvidia-vision",
        timeout_s=30.0, fallback_backend=groq))
    sent, interrupted, used, closed = [], [], set(), set()
    real_exit = httpx.AsyncHTTPTransport.__aexit__

    async def handle_async_request(self, request):
        model = json.loads(request.content)["model"]
        sent.append(model)
        used.add(id(self))
        if model != cancel_during:  # NVIDIA times out, so the chain moves on to Groq
            raise httpx.ReadTimeout("no answer", request=request)
        try:
            await asyncio.sleep(60)  # the provider has the request and has not answered
        except asyncio.CancelledError:
            interrupted.append(model)
            raise

    async def transport_exit(self, *exc):
        closed.add(id(self))
        await real_exit(self, *exc)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", handle_async_request)
    monkeypatch.setattr(httpx.AsyncHTTPTransport, "__aexit__", transport_exit)

    async def flow(client):
        rid = await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{rid}"))
        while cancel_during not in sent:
            assert not stream.done(), "the provider request never started"
            await asyncio.sleep(0.01)
        cancel = await client.post(f"/api/v1/analyze/{rid}/cancel")
        events = events_of((await asyncio.wait_for(stream, 10)).text)
        at_end = (list(interrupted), used <= closed)  # the cleanup was awaited before the stream ended
        await asyncio.sleep(0.3)  # time for any further attempt to start
        return cancel, events, at_end

    cancel, events, (interrupted_at_end, all_closed_at_end) = run(flow)
    assert cancel.status_code == 200 and events[-1]["data"]["code"] == "ANALYSIS_CANCELLED"
    assert interrupted_at_end == [cancel_during] and all_closed_at_end  # request interrupted, client closed
    assert sent[-1] == cancel_during  # nothing sent after the cancel: no fallback, no retry
    assert not any(e["event"] in ("medication_candidates_extracted", "confirmation_required") for e in events)
    assert stubs.normalizer.calls == stubs.retrieval.calls == 0


def test_a_cancel_closes_the_connection_to_the_provider(stubs, monkeypatch):
    """Real sockets: a local server that takes the whole request and never answers stands in for it."""
    from adaptive_trust_medical_rag.llm_backend.openai_vision_backend import OpenAIVisionBackend
    received, closed_by_client = asyncio.Event(), asyncio.Event()

    async def provider(reader, writer):
        head = await reader.readuntil(b"\r\n\r\n")
        await reader.readexactly(int(re.search(rb"content-length: *(\d+)", head, re.IGNORECASE).group(1)))
        received.set()  # the request, image included, has arrived
        try:
            if not await asyncio.wait_for(reader.read(1), 15):  # end of stream: the client closed it
                closed_by_client.set()
        finally:
            writer.close()  # never answers; bounded, so a failure cannot hang the server's shutdown

    async def flow(client):
        server = await asyncio.start_server(provider, "127.0.0.1", 0)
        port = server.sockets[0].getsockname()[1]
        monkeypatch.setattr(app.state, "vision_backend", OpenAIVisionBackend(
            base_url=f"http://127.0.0.1:{port}/v1", api_key="FAKE_TEST_KEY_0000", model_name="vision-local",
            timeout_s=30.0))
        async with server:
            rid = await upload(client)
            stream = asyncio.create_task(client.get(f"/api/v1/stream/{rid}"))
            await asyncio.wait_for(received.wait(), 180)  # the first request of a process also loads the models
            cancel = await client.post(f"/api/v1/analyze/{rid}/cancel")
            events = events_of((await asyncio.wait_for(stream, 10)).text)
            await asyncio.wait_for(closed_by_client.wait(), 5)  # long before its 30 s timeout
            return cancel, events

    cancel, events = run(flow)
    assert cancel.status_code == 200 and events[-1]["data"]["code"] == "ANALYSIS_CANCELLED"
    assert closed_by_client.is_set() and stubs.normalizer.calls == stubs.retrieval.calls == 0


def test_a_provider_answer_that_comes_back_after_the_cancel_is_dropped(stubs, monkeypatch):
    started = asyncio.Event()

    class Uninterruptible(Vision):
        async def extract_medications(self, image_bytes, mime_type):
            started.set()
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                pass  # a client that cannot be interrupted: its answer still comes back
            return await super().extract_medications(image_bytes, mime_type)
    late = Uninterruptible()
    monkeypatch.setattr(app.state, "vision_backend", late)

    async def flow(client):
        rid = await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{rid}"))
        await asyncio.wait_for(started.wait(), 180)  # the first request of a process also loads the models
        await client.post(f"/api/v1/analyze/{rid}/cancel")
        return events_of((await asyncio.wait_for(stream, 10)).text)

    events = run(flow)
    assert late.calls == 1 and events[-1]["data"]["code"] == "ANALYSIS_CANCELLED"  # answered, and dropped
    assert not any(e["event"] in ("medication_candidates_extracted", "confirmation_required") for e in events)
    assert stubs.normalizer.calls == stubs.retrieval.calls == 0


def test_a_cancel_while_the_image_is_read_ends_the_request_and_sends_it_nowhere(stubs, monkeypatch):
    reading, finish = threading.Event(), threading.Event()

    def slow_ocr(image_bytes, mime):
        reading.set()
        finish.wait(10)  # an OCR process in a thread cannot be interrupted; it runs out its own time
        return ImageText(OCR_OK, "Warfarin 5mg", "fixture-ocr")
    monkeypatch.setattr(app.state, "image_text_recognizer", slow_ocr)

    async def flow(client):
        rid = await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{rid}"))
        try:
            while not reading.is_set():
                await asyncio.sleep(0.01)
            loop = asyncio.get_running_loop()
            t0 = loop.time()
            cancel = await client.post(f"/api/v1/analyze/{rid}/cancel")
            events = events_of((await asyncio.wait_for(stream, 10)).text)
            return cancel, events, loop.time() - t0
        finally:
            finish.set()

    cancel, events, elapsed = run(flow)
    assert cancel.status_code == 200 and elapsed < 1.5  # not after the OCR finished
    assert events[-1]["data"]["code"] == "ANALYSIS_CANCELLED"
    assert stubs.vision.calls == 0 and stubs.normalizer.calls == 0  # the image never left this server


@pytest.mark.parametrize("first", ["confirm", "cancel"])
def test_a_confirmation_and_a_cancel_sent_together_have_exactly_one_winner(stubs, first):
    async def flow(client):
        rid = await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{rid}"))
        await awaiting(rid, stream)
        send = {"confirm": lambda: client.post(f"/api/v1/analyze/{rid}/confirm", json=BOTH),
                "cancel": lambda: client.post(f"/api/v1/analyze/{rid}/cancel")}
        order = [first, next(k for k in send if k != first)]
        replies = dict(zip(order, await asyncio.gather(*(send[k]() for k in order))))
        return replies, events_of((await asyncio.wait_for(stream, 10)).text)

    replies, events = run(flow)
    confirm, cancel = replies["confirm"].status_code, replies["cancel"].status_code
    if confirm == 200:  # the confirmation won: one analysis, which the cancel did not touch
        assert cancel in (404, 409) and stubs.normalizer.calls == 1 and events[-1]["event"] == "abstention"
    else:  # the cancel won: the confirmation was refused and nothing was analysed
        assert cancel == 200 and confirm in (404, 409)
        assert events[-1]["data"]["code"] == "ANALYSIS_CANCELLED" and stubs.normalizer.calls == 0


def test_a_cancel_after_the_analysis_ended_or_was_confirmed_changes_nothing(stubs, extraction_finished):
    async def flow(client):
        done = await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{done}"))
        await awaiting(done, stream)
        await client.post(f"/api/v1/analyze/{done}/confirm", json=BOTH)
        events = events_of((await stream).text)
        after_end = await client.post(f"/api/v1/analyze/{done}/cancel")
        # A request whose confirmation was accepted is running; it is not cancellable.
        running = await upload(client)
        extraction_finished(app, running)["confirmed_medications"] = []
        after_confirm = await client.post(f"/api/v1/analyze/{running}/cancel")
        return events, after_end, after_confirm

    events, after_end, after_confirm = run(flow)
    assert events[-1]["event"] == "abstention" and after_end.status_code == 404
    assert after_confirm.status_code == 409


def test_cancelling_one_request_never_touches_a_newer_one(stubs):
    async def flow(client):
        old, new = await upload(client), await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{new}"))
        await awaiting(new, stream)
        cancel_old = await client.post(f"/api/v1/analyze/{old}/cancel")
        confirm_new = await client.post(f"/api/v1/analyze/{new}/confirm", json=ONLY_WARFARIN)
        return cancel_old, confirm_new, events_of((await stream).text)

    cancel_old, confirm_new, events = run(flow)
    assert cancel_old.status_code == 200 and confirm_new.status_code == 200
    assert stubs.normalizer.seen == [["Warfarin"]] and events[-1]["event"] == "abstention"


# ── The OCR process, stream disconnects and request lifetime ────────────────────

def test_a_cancel_while_the_ocr_process_runs_kills_it_and_sends_the_image_nowhere(stubs, monkeypatch,
                                                                                 endless_ocr_process):
    monkeypatch.setattr(app.state, "image_text_recognizer", None)  # the real OCR code, with a stand-in process
    monkeypatch.setattr(image_grounding, "recognize_image_text", REAL_RECOGNIZER)

    async def flow(client):
        rid = await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{rid}"))
        for _ in range(18000):  # the first request of a process also loads the models
            if endless_ocr_process or stream.done():
                break
            await asyncio.sleep(0.01)
        loop = asyncio.get_running_loop()
        t0 = loop.time()
        cancel = await client.post(f"/api/v1/analyze/{rid}/cancel")
        events = events_of((await asyncio.wait_for(stream, 10)).text)
        return cancel, events, loop.time() - t0, [p.poll() is not None for p, _ in endless_ocr_process]

    cancel, events, elapsed, exited_at_end = run(flow)
    (_, image_path), = endless_ocr_process
    assert cancel.status_code == 200 and events[-1]["data"]["code"] == "ANALYSIS_CANCELLED"
    assert exited_at_end == [True] and elapsed < 5  # the process was killed, long before the 30 s OCR timeout
    assert not os.path.exists(image_path)  # its temporary image is gone
    assert stubs.vision.calls == 0 and stubs.normalizer.calls == stubs.retrieval.calls == 0


def test_a_stream_opened_after_its_deadline_is_refused_even_if_its_timer_is_late(stubs, monkeypatch):
    monkeypatch.setattr(analyze_routes, "STREAM_OPEN_TTL_S", -1.0)  # already past its deadline
    monkeypatch.setattr(analyze_routes, "_drop_if_unopened", lambda pending, rid: None)  # a busy loop's timer

    async def flow(client):
        rid = await upload(client)
        return rid, events_of((await client.get(f"/api/v1/stream/{rid}")).text)

    rid, events = run(flow)
    assert events[-1]["data"]["code"] == "REQUEST_EXPIRED" and rid not in app.state.pending_analyses
    assert stubs.vision.calls == 0


def test_an_unopened_upload_is_dropped_at_its_deadline_with_no_further_request(stubs, monkeypatch):
    monkeypatch.setattr(analyze_routes, "STREAM_OPEN_TTL_S", 0.2)

    async def flow(client):
        rid = await upload(client)
        held = rid in app.state.pending_analyses
        image_bytes = app.state.pending_analyses[rid]["image_bytes"]
        await asyncio.sleep(0.6)  # an idle server: no request of any kind meanwhile
        gone = rid not in app.state.pending_analyses
        still_held_by = [r for r in gc.get_referrers(image_bytes) if isinstance(r, dict)]  # no registry entry
        late = (await client.get(f"/api/v1/stream/{rid}"), await client.post(f"/api/v1/analyze/{rid}/confirm", json=BOTH),
                await client.post(f"/api/v1/analyze/{rid}/cancel"))
        return held, gone, still_held_by, late

    held, gone, still_held_by, (stream, confirm, cancel) = run(flow)
    assert held and gone and still_held_by == []  # removed by its own deadline, uploaded image included
    assert events_of(stream.text)[-1]["data"]["code"] == "NOT_FOUND"
    assert (confirm.status_code, cancel.status_code) == (404, 404) and stubs.vision.calls == 0


def test_a_request_whose_stream_opened_in_time_is_not_touched_by_its_open_deadline(stubs, monkeypatch):
    monkeypatch.setattr(analyze_routes, "STREAM_OPEN_TTL_S", 0.2)

    async def flow(client):
        rid = await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{rid}"))
        await awaiting(rid, stream)
        await asyncio.sleep(0.5)  # past the open deadline, while it waits for the user
        held = rid in app.state.pending_analyses
        confirm = await client.post(f"/api/v1/analyze/{rid}/confirm", json=BOTH)
        return held, confirm, events_of((await stream).text)

    held, confirm, events = run(flow)
    assert held and confirm.status_code == 200
    assert stubs.normalizer.calls == 1 and events[-1]["event"] == "abstention"


def test_work_that_will_not_stop_is_abandoned_at_the_bound_and_its_late_answer_dropped(stubs, monkeypatch, caplog):
    monkeypatch.setattr(live_application, "CANCEL_CLEANUP_S", 0.3)
    started, answered = asyncio.Event(), []

    class Stubborn(Vision):  # ignores every cancel for a while, then answers anyway
        async def extract_medications(self, image_bytes, mime_type):
            started.set()
            end = asyncio.get_running_loop().time() + 1.5
            while asyncio.get_running_loop().time() < end:
                try:
                    await asyncio.sleep(0.05)
                except asyncio.CancelledError:
                    continue
            answered.append(True)
            return await super().extract_medications(image_bytes, mime_type)
    monkeypatch.setattr(app.state, "vision_backend", Stubborn())

    async def flow(client):
        rid = await upload(client)
        stream = asyncio.create_task(client.get(f"/api/v1/stream/{rid}"))
        await asyncio.wait_for(started.wait(), 180)  # the first request of a process also loads the models
        loop = asyncio.get_running_loop()
        t0 = loop.time()
        await client.post(f"/api/v1/analyze/{rid}/cancel")
        events = events_of((await asyncio.wait_for(stream, 10)).text)
        elapsed = loop.time() - t0
        await asyncio.sleep(1.5)  # let the stubborn call finish late
        return rid, events, elapsed

    with caplog.at_level(logging.WARNING, logger=live_application.__name__):
        rid, events, elapsed = run(flow)
    assert events[-1]["data"]["code"] == "ANALYSIS_CANCELLED" and elapsed < 1.2  # the bound, not the call
    assert "did not stop within" in caplog.text  # a safe diagnostic, not a success
    assert answered == [True]  # it did answer, late...
    assert not any(e["event"] in ("medication_candidates_extracted", "confirmation_required") for e in events)
    assert rid not in app.state.pending_analyses and stubs.normalizer.calls == stubs.retrieval.calls == 0  # ...unused


def test_an_unconfirmed_request_ends_at_its_deadline_and_a_late_confirmation_is_refused(stubs):
    async def flow(client):
        rid = await upload(client)
        events = events_of((await client.get(f"/api/v1/stream/{rid}")).text)  # 2 s deadline in tests
        return rid, events, await client.post(f"/api/v1/analyze/{rid}/confirm", json=BOTH)

    rid, events, late = run(flow)
    assert events[-1]["data"]["code"] == "CONFIRMATION_TIMEOUT" and rid not in app.state.pending_analyses
    assert late.status_code == 404 and stubs.normalizer.calls == 0


@pytest.fixture
def live_server():
    """The app on a real uvicorn server (a real socket a client can drop), in a thread."""
    import uvicorn
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning", lifespan="off"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + 30
    while not server.started:
        assert time.monotonic() < deadline and thread.is_alive(), "the test server did not start"
        time.sleep(0.05)
    yield f"http://127.0.0.1:{server.servers[0].sockets[0].getsockname()[1]}"
    server.should_exit = True
    thread.join(15)


class RemovalProbe(dict):
    """The request registry, recording what a request's owned work looked like the moment it was removed."""

    def __init__(self, probe):
        super().__init__()
        self.probe, self.at_removal = probe, {}

    def pop(self, key, *default):
        if key in self:
            self.at_removal.setdefault(key, self.probe())
        return super().pop(key, *default)


@pytest.mark.parametrize("close_while", ["awaiting_confirmation", "ocr_running", "vision_running"])
def test_a_client_that_drops_its_stream_ends_the_request_after_its_own_work_is_stopped(
        stubs, monkeypatch, live_server, endless_ocr_process, close_while):
    """No cancel request at all: the browser closed, reloaded or lost the page."""
    sent, interrupted, used, closed = [], [], set(), set()
    if close_while == "ocr_running":
        monkeypatch.setattr(app.state, "image_text_recognizer", None)
        monkeypatch.setattr(image_grounding, "recognize_image_text", REAL_RECOGNIZER)
    if close_while == "vision_running":  # the real vision client; only httpx's network send is replaced
        from adaptive_trust_medical_rag.llm_backend.openai_vision_backend import OpenAIVisionBackend
        monkeypatch.setattr(app.state, "vision_backend", OpenAIVisionBackend(
            base_url="https://nvidia.invalid/v1", api_key="FAKE_TEST_KEY_0000", model_name="nvidia-vision",
            timeout_s=30.0))
        real_exit = httpx.AsyncHTTPTransport.__aexit__

        async def handle_async_request(self, request):
            sent.append(1)
            used.add(id(self))
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                interrupted.append(1)
                raise

        async def transport_exit(self, *exc):
            closed.add(id(self))
            await real_exit(self, *exc)
        monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", handle_async_request)
        monkeypatch.setattr(httpx.AsyncHTTPTransport, "__aexit__", transport_exit)

    def owned_work():
        if close_while == "ocr_running":
            (proc, path), = endless_ocr_process
            return {"process_exited": proc.poll() is not None, "image_removed": not os.path.exists(path)}
        if close_while == "vision_running":
            return {"request_interrupted": bool(interrupted), "client_closed": bool(used) and used <= closed}
        return {}
    registry = RemovalProbe(owned_work)
    monkeypatch.setattr(app.state, "pending_analyses", registry)

    with httpx.Client(base_url=live_server, timeout=300) as client:
        files = {"image": ("rx.png", image(), "image/png")}
        rid = client.post("/api/v1/analyze/prescription", files=files).json()["request_id"]
        with client.stream("GET", f"/api/v1/stream/{rid}") as stream:
            for line in stream.iter_lines():
                if close_while == "awaiting_confirmation" and line == "event: confirmation_required":
                    break
                if close_while != "awaiting_confirmation" and '"stage": "extracting"' in line:
                    started = endless_ocr_process if close_while == "ocr_running" else sent
                    deadline = time.monotonic() + 10
                    while not started and time.monotonic() < deadline:
                        time.sleep(0.01)
                    break
        # Leaving the block closes the connection, as a closed tab does.
        t0, deadline = time.monotonic(), time.monotonic() + 10
        while rid in registry and time.monotonic() < deadline:
            time.sleep(0.01)
        elapsed = time.monotonic() - t0
        late = (client.post(f"/api/v1/analyze/{rid}/confirm", json=BOTH).status_code,
                client.post(f"/api/v1/analyze/{rid}/cancel").status_code)
    assert rid not in registry and elapsed < 5  # not the 2 s / 300 s deadlines
    # When the request was removed, the work it owned had already stopped (not merely been told to).
    assert all(registry.at_removal[rid].values()), registry.at_removal[rid]
    assert late == (404, 404)
    assert stubs.normalizer.calls == stubs.retrieval.calls == 0
    if close_while == "ocr_running":
        assert stubs.vision.calls == 0
