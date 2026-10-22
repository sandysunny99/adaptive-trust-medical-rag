"""Vision extraction failures: classification, the optional fallback model, and bounded waits.

No failure ever produces a medication list. HTTP responses are simulated; no provider is called.
"""

from __future__ import annotations

import asyncio
import json
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


def test_a_stalled_request_is_retried_once_on_the_same_model():
    result, calls = extract(backend(), httpx.ReadTimeout("stalled"), Resp(200, GOOD))
    assert calls == ["vision-primary", "vision-primary"]
    assert [c.normalized_text for c in result.candidate_medications] == ["lisinopril", "spironolactone"]
    assert [a["outcome"] for a in result.attempts] == ["failed", "success"]
    assert result.attempts[0]["failure_class"] == "TIMEOUT" and result.model_used == "vision-primary"


def test_after_the_retry_the_fallback_model_is_tried_once():
    result, calls = extract(backend("vision-fallback"), httpx.ReadTimeout("a"), httpx.ReadTimeout("b"),
                            Resp(200, GOOD))
    assert calls == ["vision-primary", "vision-primary", "vision-fallback"]
    assert result.model_used == "vision-fallback"


def test_a_timeout_without_a_fallback_is_a_timeout_with_no_medications():
    err, calls = extract(backend(), httpx.ReadTimeout("slow"), httpx.ReadTimeout("slow"))
    assert isinstance(err, ModelExecutionError) and err.failure_class == FailureClass.TIMEOUT
    assert "did not answer within 5 s" in str(err) and "after 2 attempts" in str(err)
    assert calls == ["vision-primary", "vision-primary"]
    assert [a["failure_class"] for a in err.attempts] == ["TIMEOUT", "TIMEOUT"]


def test_when_every_attempt_times_out_the_error_is_reported_and_nothing_is_extracted():
    err, calls = extract(backend("vision-fallback"), *[httpx.ReadTimeout("x")] * 4)
    assert isinstance(err, ModelExecutionError) and err.failure_class == FailureClass.TIMEOUT
    assert calls == ["vision-primary", "vision-primary", "vision-fallback", "vision-fallback"]


def test_the_total_deadline_bounds_every_attempt():
    b = OpenAIVisionBackend(base_url="https://example.invalid/v1", api_key="FAKE_TEST_KEY_0000",
                            model_name="vision-primary", timeout_s=30.0, deadline_s=40.0)
    clock, seen = [0.0], []

    async def post(self, url, json=None, headers=None):
        seen.append(self.timeout.read)
        clock[0] += self.timeout.read  # the request stalls for its whole timeout
        raise httpx.ReadTimeout("stalled")

    with patch("httpx.AsyncClient.post", new=post), patch(
            "adaptive_trust_medical_rag.llm_backend.openai_vision_backend.time.monotonic", new=lambda: clock[0]):
        with pytest.raises(ModelExecutionError) as exc:
            asyncio.run(b.extract_medications(b"img", "image/png"))
    # The retry gets only what is left of the 40 s deadline, never a fresh 30 s.
    assert seen == [30.0, 10.0] and clock[0] == 40.0
    assert exc.value.failure_class == FailureClass.TIMEOUT


@pytest.mark.parametrize(("status", "fc"), [
    (404, FailureClass.MODEL_NOT_FOUND), (403, FailureClass.AUTHORIZATION),
    (400, FailureClass.INVALID_REQUEST), (503, FailureClass.TRANSIENT_PROVIDER)])
def test_vision_http_errors_are_classified(status, fc):
    err, _ = extract(backend(), *[Resp(status, text="detail for account 'acct-123'")] * 2)
    assert err.failure_class == fc


@pytest.mark.parametrize(("first", "expected"), [
    (Resp(401), ["vision-primary"]), (Resp(429), ["vision-primary"]), (Resp(400), ["vision-primary"]),
    (Resp(404), ["vision-primary", "vision-fallback"]),          # missing model: no retry, fallback
    (Resp(502), ["vision-primary", "vision-primary"])])         # transient: one retry succeeds
def test_retry_and_fallback_follow_the_failure_class(first, expected):
    _, calls = extract(backend("vision-fallback"), first, Resp(200, GOOD))
    assert calls == expected


def test_unparseable_vision_output_is_a_schema_error_not_a_medication_list():
    bad = {"choices": [{"message": {"content": "I think it says lisinopril."}}]}
    err, _ = extract(backend("vision-fallback"), Resp(200, bad))
    assert isinstance(err, ModelExecutionError) and err.failure_class == FailureClass.SCHEMA_ERROR


def test_an_unconfirmed_extraction_ends_with_an_explicit_timeout(monkeypatch):
    monkeypatch.setenv("TESTING", "1")  # 2 s confirmation window

    class Vision:
        provider_name, model_name = "mock_vision", "mock-model"

        async def extract_medications(self, image_bytes, mime):
            return SimpleNamespace(candidate_medications=[], warnings=[], raw_text="")

    state = SimpleNamespace(vision_backend=Vision(), claim_verifier=object(), retrieval_engine=object(),
                            model_init_errors={})
    analysis = {"confirmation_event": asyncio.Event()}

    async def collect():
        return [e async for e in LiveMedicalRAGService(state).execute(
            "req-img", [], None, 0, image_bytes=b"img", image_meta={"content_type": "image/png"},
            analysis_state=analysis)]

    events = asyncio.run(collect())
    assert events[-1]["event"] == "error" and events[-1]["data"]["code"] == "CONFIRMATION_TIMEOUT"
    assert analysis["finished"] is True
    assert not any(e["event"] in ("answer", "rxnorm") for e in events)


def test_a_vision_failure_reports_its_class_and_produces_no_candidates(monkeypatch):
    class Vision:
        provider_name, model_name = "mock_vision", "mock-model"

        async def extract_medications(self, image_bytes, mime):
            err = ModelExecutionError("Vision Provider Timeout", status_code="TIMEOUT")
            err.failure_class = FailureClass.TIMEOUT
            raise err

    state = SimpleNamespace(vision_backend=Vision(), claim_verifier=object(), retrieval_engine=object(),
                            model_init_errors={})

    async def collect():
        return [e async for e in LiveMedicalRAGService(state).execute(
            "req-img", [], None, 0, image_bytes=b"img", image_meta={"content_type": "image/png"},
            analysis_state={"confirmation_event": asyncio.Event()})]

    events = asyncio.run(collect())
    (err,) = [e["data"] for e in events if e["event"] == "error"]
    assert (err["code"], err["failure_class"]) == ("VISION_EXTRACTION_ERROR", "TIMEOUT")
    assert not any(e["event"] == "medication_candidates_extracted" for e in events)
