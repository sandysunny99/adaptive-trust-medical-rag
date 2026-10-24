"""Vision extraction failures: classification, the optional fallback model, and bounded waits.

No failure ever produces a medication list. HTTP responses are simulated; no provider is called.
"""

from __future__ import annotations

import asyncio
import json
import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_backend.openai_vision_backend import OpenAIVisionBackend
from adaptive_trust_medical_rag.llm_routing.types import FailureClass
from adaptive_trust_medical_rag.services.live_application import LiveMedicalRAGService

GOOD = {"choices": [{"message": {"content": json.dumps({
    "raw_text": "SYNTHETIC Rx Lisinopril 10 mg Spironolactone 25 mg",
    "candidate_medications": [
        {"raw_text": "Lisinopril 10 mg", "normalized_text": "lisinopril", "confidence": "HIGH"},
        {"raw_text": "Spironolactone 25 mg", "normalized_text": "spironolactone", "confidence": "HIGH"},
    ], "warnings": []})}}]}


class Resp:
    def __init__(self, status, body=None, text=""):
        self.status_code, self._body, self.text = status, body, text

    def json(self):
        return self._body


def backend(fallback=None):
    return OpenAIVisionBackend(base_url="https://example.invalid/v1", api_key="FAKE_TEST_KEY_0000",
                               model_name="vision-primary", timeout_s=5.0, fallback_model=fallback)


def extract(b, *responses):
    """Run one extraction; each response is a Resp or an exception raised by the HTTP call."""
    calls = []

    async def post(self, url, json=None, headers=None):
        calls.append(json["model"])
        r = responses[len(calls) - 1]
        if isinstance(r, Exception):
            raise r
        return r

    with patch("httpx.AsyncClient.post", new=post):
        try:
            return asyncio.run(b.extract_medications(b"\x89PNG", "image/png")), calls
        except ModelExecutionError as e:
            return e, calls


def test_a_stalled_request_is_not_retried_on_the_same_model():
    # A stall costs a whole timeout; the user waits on it, so it moves on rather than waiting again.
    err, calls = extract(backend(), httpx.ReadTimeout("stalled"), Resp(200, GOOD))
    assert calls == ["vision-primary"]
    assert isinstance(err, ModelExecutionError) and err.failure_class == FailureClass.TIMEOUT


def test_a_stalled_request_moves_straight_to_the_fallback_model():
    result, calls = extract(backend("vision-fallback"), httpx.ReadTimeout("a"), Resp(200, GOOD))
    assert calls == ["vision-primary", "vision-fallback"]
    assert result.model_used == "vision-fallback"
    assert [a["outcome"] for a in result.attempts] == ["failed", "success"]


def test_a_timeout_without_a_fallback_is_a_timeout_with_no_medications():
    err, calls = extract(backend(), httpx.ReadTimeout("slow"))
    assert isinstance(err, ModelExecutionError) and err.failure_class == FailureClass.TIMEOUT
    assert "did not answer within 5 s" in str(err)
    assert calls == ["vision-primary"]
    assert [a["failure_class"] for a in err.attempts] == ["TIMEOUT"]


def test_when_every_attempt_times_out_the_error_is_reported_and_nothing_is_extracted():
    err, calls = extract(backend("vision-fallback"), *[httpx.ReadTimeout("x")] * 2)
    assert isinstance(err, ModelExecutionError) and err.failure_class == FailureClass.TIMEOUT
    assert calls == ["vision-primary", "vision-fallback"]


def test_the_total_deadline_bounds_every_attempt():
    b = OpenAIVisionBackend(base_url="https://example.invalid/v1", api_key="FAKE_TEST_KEY_0000",
                            model_name="vision-primary", timeout_s=30.0, deadline_s=40.0,
                            fallback_model="vision-fallback")
    clock, seen = [0.0], []

    async def post(self, url, json=None, headers=None):
        seen.append(self.timeout.read)
        clock[0] += self.timeout.read  # the request stalls for its whole timeout
        raise httpx.ReadTimeout("stalled")

    with patch("httpx.AsyncClient.post", new=post), patch(
            "adaptive_trust_medical_rag.llm_backend.openai_vision_backend.time.monotonic", new=lambda: clock[0]):
        with pytest.raises(ModelExecutionError) as exc:
            asyncio.run(b.extract_medications(b"img", "image/png"))
    # The fallback gets only what is left of the 40 s deadline, never a fresh 30 s.
    assert seen == [30.0, 10.0] and clock[0] == 40.0
    assert exc.value.failure_class == FailureClass.TIMEOUT


@pytest.mark.parametrize(("status", "fc"), [
    (404, FailureClass.MODEL_NOT_FOUND), (403, FailureClass.AUTHORIZATION),
    (400, FailureClass.INVALID_REQUEST), (503, FailureClass.TRANSIENT_PROVIDER)])
def test_vision_http_errors_are_classified(status, fc):
    err, _ = extract(backend(), *[Resp(status, text="detail for account 'acct-123'")] * 2)
    assert err.failure_class == fc


# A synthetic "echoed request": what a provider's error body could carry back.
SENTINEL = "SENTINEL-ECHO-7f3a synthetic prescription text Warfarin 5 mg"


@pytest.mark.parametrize(("status", "fc", "attempts"), [
    (400, FailureClass.INVALID_REQUEST, 1), (404, FailureClass.MODEL_NOT_FOUND, 1),
    (503, FailureClass.TRANSIENT_PROVIDER, 2)])                 # a transient error is still retried once
def test_a_vision_error_body_is_never_logged(caplog, status, fc, attempts):
    with caplog.at_level(logging.DEBUG, logger="adaptive_trust_medical_rag"):
        err, calls = extract(backend(), *[Resp(status, text=f"could not process request: {SENTINEL}")] * 2)
    assert isinstance(err, ModelExecutionError) and err.failure_class == fc and len(calls) == attempts
    assert SENTINEL not in caplog.text and SENTINEL not in str(err)
    assert f"Vision provider vision-primary HTTP {status}" in caplog.text  # who failed, and how


def test_a_reply_quoting_the_prescription_reaches_neither_the_log_nor_the_user(monkeypatch, ocr_reads, caplog):
    """A 200 whose content is prose quoting the image fails as SCHEMA_ERROR through the real client and pipeline."""
    prose = Resp(200, {"choices": [{"message": {"content": f"The prescription reads: {SENTINEL}."}}]})

    async def post(self, url, json=None, headers=None):
        return prose
    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    state = SimpleNamespace(vision_backend=backend(), claim_verifier=object(), retrieval_engine=object(),
                            model_init_errors={}, image_text_recognizer=ocr_reads("SYNTHETIC Rx Warfarin 5 mg"))

    async def collect():
        return [e async for e in LiveMedicalRAGService(state).execute(
            "req-img", [], None, 0, image_bytes=b"img", image_meta={"content_type": "image/png"},
            analysis_state={"confirmation_event": asyncio.Event()})]

    with caplog.at_level(logging.DEBUG, logger="adaptive_trust_medical_rag"):
        events = asyncio.run(collect())
    (err,) = [e["data"] for e in events if e["event"] == "error"]
    assert (err["code"], err["failure_class"]) == ("VISION_EXTRACTION_ERROR", "SCHEMA_ERROR")
    assert SENTINEL not in json.dumps(events) and SENTINEL not in caplog.text
    assert not any(e["event"] == "medication_candidates_extracted" for e in events)


@pytest.mark.parametrize(("first", "expected"), [
    (Resp(401), ["vision-primary"]), (Resp(429), ["vision-primary"]), (Resp(400), ["vision-primary"]),
    (Resp(404), ["vision-primary", "vision-fallback"]),          # missing model: no retry, fallback
    (Resp(502), ["vision-primary", "vision-primary"])])         # transient: one retry succeeds
def test_retry_and_fallback_follow_the_failure_class(first, expected):
    _, calls = extract(backend("vision-fallback"), first, Resp(200, GOOD))
    assert calls == expected


def reply(content: str) -> Resp:
    return Resp(200, {"choices": [{"message": {"content": content}}]})


# The shape NVIDIA returned for a real upload on 2026-10-22: a JSON object, then extra data.
OBJECT_THEN_EXTRA = (json.dumps({"raw_text": "x", "candidate_medications": [], "warnings": []})
                     + "\n{\"note\": \"second object\"}")


@pytest.mark.parametrize("content", ["I think it says lisinopril.", OBJECT_THEN_EXTRA,
                                     '{"raw_text": "x", "candidate_medications": [', ""])
def test_unparseable_output_is_a_schema_error_and_never_a_medication_list(content):
    err, calls = extract(backend(), reply(content))
    assert isinstance(err, ModelExecutionError) and err.failure_class == FailureClass.SCHEMA_ERROR
    assert calls == ["vision-primary"]  # malformed output is not retried on the same model


def test_malformed_output_moves_to_the_other_provider_once():
    result, calls = extract(with_groq(), reply(OBJECT_THEN_EXTRA), Resp(200, GOOD))
    assert calls == ["vision-primary", "groq-vision"]
    assert (result.provider_used, result.model_used) == ("groq_vision", "groq-vision")
    assert [c.normalized_text for c in result.candidate_medications] == ["lisinopril", "spironolactone"]


def test_when_both_providers_reply_malformed_nothing_is_extracted():
    err, calls = extract(with_groq(), reply(OBJECT_THEN_EXTRA), reply(OBJECT_THEN_EXTRA))
    assert isinstance(err, ModelExecutionError) and err.failure_class == FailureClass.SCHEMA_ERROR
    assert calls == ["vision-primary", "groq-vision"]
    assert [a["provider"] for a in err.attempts] == ["nvidia_vision", "groq_vision"]


def test_the_extra_data_log_names_its_shape_never_its_content(caplog):
    secret = "Patient Jane Synthetic DOB 01/01/1970"
    # The "Extra data" path needs a reply that starts with { and ends with }, as NVIDIA's did.
    content = (json.dumps({"raw_text": secret, "candidate_medications": [], "warnings": []})
               + json.dumps({"note": secret}))
    with caplog.at_level("WARNING"):
        extract(backend(), reply(content))
    assert "Extra data" in caplog.text and "after error: json" in caplog.text and secret not in caplog.text


def test_an_unconfirmed_extraction_ends_with_an_explicit_timeout(monkeypatch, ocr_reads):
    monkeypatch.setenv("TESTING", "1")  # 2 s confirmation window

    class Vision:
        provider_name, model_name = "mock_vision", "mock-model"

        async def extract_medications(self, image_bytes, mime):
            return SimpleNamespace(candidate_medications=[SimpleNamespace(
                raw_text="Warfarin 5mg", normalized_text="warfarin", confidence=SimpleNamespace(value="HIGH"))],
                warnings=[], raw_text="Warfarin 5mg")

    # A candidate the image text supports, which nobody confirms (no candidate at all never waits).
    state = SimpleNamespace(vision_backend=Vision(), claim_verifier=object(), retrieval_engine=object(),
                            model_init_errors={}, image_text_recognizer=ocr_reads("Warfarin 5mg"))
    analysis = {"confirmation_event": asyncio.Event()}

    async def collect():
        return [e async for e in LiveMedicalRAGService(state).execute(
            "req-img", [], None, 0, image_bytes=b"img", image_meta={"content_type": "image/png"},
            analysis_state=analysis)]

    events = asyncio.run(collect())
    assert events[-1]["event"] == "error" and events[-1]["data"]["code"] == "CONFIRMATION_TIMEOUT"
    assert analysis["finished"] is True
    assert not any(e["event"] in ("answer", "rxnorm") for e in events)


def test_a_vision_failure_reports_its_class_and_produces_no_candidates(monkeypatch, ocr_reads):
    class Vision:
        provider_name, model_name = "mock_vision", "mock-model"

        async def extract_medications(self, image_bytes, mime):
            err = ModelExecutionError("Vision Provider Timeout", status_code="TIMEOUT")
            err.failure_class = FailureClass.TIMEOUT
            raise err

    # The image has readable text, so it may go to the vision provider, which then fails.
    state = SimpleNamespace(vision_backend=Vision(), claim_verifier=object(), retrieval_engine=object(),
                            model_init_errors={}, image_text_recognizer=ocr_reads("SYNTHETIC Rx Warfarin 5 mg"))

    async def collect():
        return [e async for e in LiveMedicalRAGService(state).execute(
            "req-img", [], None, 0, image_bytes=b"img", image_meta={"content_type": "image/png"},
            analysis_state={"confirmation_event": asyncio.Event()})]

    events = asyncio.run(collect())
    (err,) = [e["data"] for e in events if e["event"] == "error"]
    assert (err["code"], err["failure_class"]) == ("VISION_EXTRACTION_ERROR", "TIMEOUT")
    assert not any(e["event"] == "medication_candidates_extracted" for e in events)


# ── Cross-provider fallback (Groq vision after NVIDIA) ───────────────────────

def with_groq():
    groq = OpenAIVisionBackend(base_url="https://groq.invalid/v1", api_key="FAKE_TEST_KEY_0001",
                               model_name="groq-vision", provider_name="groq_vision", timeout_s=5.0)
    return OpenAIVisionBackend(base_url="https://example.invalid/v1", api_key="FAKE_TEST_KEY_0000",
                               model_name="vision-primary", timeout_s=5.0, fallback_backend=groq)


def test_groq_serves_after_nvidia_stalls_and_the_result_names_it():
    # One bounded NVIDIA attempt, then Groq once: no second wait on the stalled model.
    result, calls = extract(with_groq(), httpx.ReadTimeout("a"), Resp(200, GOOD))
    assert calls == ["vision-primary", "groq-vision"]
    assert (result.provider_used, result.model_used) == ("groq_vision", "groq-vision")
    assert [a["provider"] for a in result.attempts] == ["nvidia_vision", "groq_vision"]
    assert [c.normalized_text for c in result.candidate_medications] == ["lisinopril", "spironolactone"]


def test_when_nvidia_stalls_and_groq_fails_the_extraction_fails_once_with_no_medications():
    err, calls = extract(with_groq(), httpx.ReadTimeout("a"), httpx.ReadTimeout("b"))
    assert isinstance(err, ModelExecutionError) and err.failure_class == FailureClass.TIMEOUT
    assert calls == ["vision-primary", "groq-vision"]
    assert [a["provider"] for a in err.attempts] == ["nvidia_vision", "groq_vision"]


def test_a_network_error_is_retried_once_on_the_same_model():
    result, calls = extract(backend("vision-fallback"), httpx.ConnectError("reset"), Resp(200, GOOD))
    assert calls == ["vision-primary", "vision-primary"] and result.model_used == "vision-primary"


def test_a_valid_reply_with_no_medications_is_an_empty_result_not_a_fallback():
    empty = reply(json.dumps({"raw_text": "SYNTHETIC", "candidate_medications": [], "warnings": []}))
    result, calls = extract(with_groq(), empty)
    assert calls == ["vision-primary"] and result.candidate_medications == []
    assert result.provider_used == "nvidia_vision"


@pytest.mark.parametrize("first", [Resp(401), Resp(429), Resp(400)])
def test_groq_is_not_used_when_nvidia_fails_for_a_non_availability_reason(first):
    err, calls = extract(with_groq(), first, Resp(200, GOOD))
    assert isinstance(err, ModelExecutionError) and calls == ["vision-primary"]


def test_groq_is_skipped_when_the_deadline_is_used_up():
    b = with_groq()
    b.deadline_s = 5.0
    clock = [0.0]

    async def post(self, url, json=None, headers=None):
        clock[0] += self.timeout.read
        raise httpx.ReadTimeout("stalled")

    with patch("httpx.AsyncClient.post", new=post), patch(
            "adaptive_trust_medical_rag.llm_backend.openai_vision_backend.time.monotonic", new=lambda: clock[0]):
        with pytest.raises(ModelExecutionError) as exc:
            asyncio.run(b.extract_medications(b"img", "image/png"))
    # NVIDIA's 5 s used the whole 5 s budget: Groq never started.
    assert [a["provider"] for a in exc.value.attempts] == ["nvidia_vision"]


def test_the_app_wires_groq_vision_as_the_fallback_and_it_can_be_disabled(monkeypatch):
    from adaptive_trust_medical_rag.api.app import DEFAULT_GROQ_VISION_MODEL, create_app
    monkeypatch.setenv("NVIDIA_OCR_API_KEY", "FAKE_TEST_KEY_0000")
    monkeypatch.setenv("GROQ_API_KEY", "FAKE_TEST_KEY_0001")
    monkeypatch.delenv("GROQ_VISION_MODEL", raising=False)
    vision = create_app().state.vision_backend
    assert vision.provider_name == "nvidia_vision"
    assert (vision.fallback_backend.provider_name, vision.fallback_backend.model_name) == (
        "groq_vision", DEFAULT_GROQ_VISION_MODEL)
    monkeypatch.setenv("GROQ_VISION_MODEL", "")
    assert create_app().state.vision_backend.fallback_backend is None


@pytest.mark.parametrize(("text_setting", "value"), [
    ("LLM_PROVIDER", "cloudflare"), ("LLM_FALLBACK_PROVIDERS", "cloudflare"), ("LLM_FAILOVER_ENABLED", "false")])
def test_text_llm_settings_do_not_change_the_vision_chain(monkeypatch, text_setting, value):
    # Text fallback and vision fallback are separate settings: remapping one never moves the other.
    from adaptive_trust_medical_rag.api.app import DEFAULT_GROQ_VISION_MODEL, create_app
    monkeypatch.setenv("NVIDIA_OCR_API_KEY", "FAKE_TEST_KEY_0000")
    monkeypatch.setenv("GROQ_API_KEY", "FAKE_TEST_KEY_0001")
    monkeypatch.delenv("GROQ_VISION_MODEL", raising=False)
    monkeypatch.setenv(text_setting, value)
    vision = create_app().state.vision_backend
    assert (vision.provider_name, vision.model_name) == ("nvidia_vision", "meta/llama-3.2-11b-vision-instruct")
    assert (vision.fallback_backend.provider_name, vision.fallback_backend.model_name) == (
        "groq_vision", DEFAULT_GROQ_VISION_MODEL)


def test_concurrent_model_loads_share_one_load(monkeypatch):
    import threading
    import time as _time
    from adaptive_trust_medical_rag.services import live_application
    loads = []

    def slow_load(state):
        loads.append(1)
        _time.sleep(0.2)
        state.retrieval_engine = state.retrieval_engine or object()

    def guarded(state):  # the real loader skips work already done; this stand-in does the same
        if getattr(state, "retrieval_engine", None) is None:
            slow_load(state)

    monkeypatch.setattr(live_application, "_load_models", guarded)
    state = SimpleNamespace(retrieval_engine=None)
    threads = [threading.Thread(target=live_application._lazy_init_models, args=(state,)) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(loads) == 1
