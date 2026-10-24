"""Regression tests for the 2026-10-22 audit of the live application.

Each test pins one defect found in the audit, or one contract the audit confirmed:

* RequestDrugMap: the live path recognises the request's own medication names in claims, while a
  plain dict (every research caller) keeps the fixed drug pattern and so keeps its results.
* A 200 response that is not a chat completion is a classified SCHEMA_ERROR the router can fail
  over on, not a raw exception that bypasses the attempt log.
* The vision model that served an extraction travels on the result; the shared backend attribute
  can belong to another, concurrent request.
* Provider settings the live router does not read are reported at startup, without changing the
  provider order.
* provenance_status is computed from the registered SHA-256, never assumed.
* The production resolver loads no pending record (no candidate is in the live folder).

No real provider, network or model is used.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from adaptive_trust_medical_rag.api import app as app_module
from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_backend.live_provider_router import LiveProviderRouter
from adaptive_trust_medical_rag.llm_backend.openai_compatible_backend import OpenAICompatibleBackend
from adaptive_trust_medical_rag.llm_backend.openai_vision_backend import OpenAIVisionBackend
from adaptive_trust_medical_rag.llm_routing.types import FailureClass
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate
from adaptive_trust_medical_rag.services import live_relationships
from adaptive_trust_medical_rag.services.live_application import _provenance_status
from adaptive_trust_medical_rag.verification.canonical_identity import (
    CanonicalDirection,
    CanonicalMatchStatus,
    CanonicalRelationshipIdentity,
    RequestDrugMap,
    compare_identity,
    extract_claim_identity,
)

FAKE_KEY = "FAKE_TEST_KEY_NOT_A_SECRET_0000"
ROOT = Path(__file__).resolve().parents[1]
REL_DIR = ROOT / "data" / "live_medical" / "relationships"
CLAIM = "Lisinopril interacts with spironolactone and can increase the risk of hyperkalemia."


def live_map(**names: str) -> RequestDrugMap:
    m = RequestDrugMap()
    m.update(names)
    return m


# ── Phase B: canonical identity contract ─────────────────────────────────────

def test_the_live_map_gives_a_claim_naming_a_requested_drug_an_identity():
    identity = extract_claim_identity(CLAIM, live_map(lisinopril="29046", spironolactone="9997"))
    assert identity is not None
    assert (identity.subject_rxcui, identity.object_rxcui) == ("29046", "9997")
    assert identity.predicate == "INTERACTION" and identity.direction == CanonicalDirection.A_TO_B


def test_a_research_callers_plain_dict_keeps_the_fixed_pattern_and_its_none_result():
    # spironolactone is not in the fixed pattern, so a research caller still gets None.
    assert extract_claim_identity(CLAIM, {"lisinopril": "29046", "spironolactone": "9997"}) is None


def test_drug_order_in_the_claim_is_kept_never_swapped_to_match_a_record():
    reversed_claim = "Spironolactone interacts with lisinopril and can increase potassium."
    identity = extract_claim_identity(reversed_claim, live_map(lisinopril="29046", spironolactone="9997"))
    assert (identity.subject_rxcui, identity.object_rxcui) == ("9997", "29046")
    source = CanonicalRelationshipIdentity("29046", "9997", "INTERACTION", CanonicalDirection.A_TO_B)
    status, _ = compare_identity(source, identity)
    assert status == CanonicalMatchStatus.MISMATCH  # direction-sensitive comparison is unchanged


def test_a_mention_without_an_rxcui_gives_no_identity():
    # A name the request did not resolve cannot be given an RxCUI from its display text.
    assert extract_claim_identity(CLAIM, live_map(lisinopril="29046")) is None


def test_a_combination_product_keeps_its_own_rxcui_and_cannot_match_a_single_ingredient_record():
    combo = live_map(**{"lisinopril / hydrochlorothiazide": "214618", "spironolactone": "9997"})
    claim = "Lisinopril / hydrochlorothiazide interacts with spironolactone."
    identity = extract_claim_identity(claim, combo)
    assert identity is not None and identity.subject_rxcui == "214618"
    source = CanonicalRelationshipIdentity("29046", "9997", "INTERACTION", CanonicalDirection.A_TO_B)
    assert compare_identity(source, identity)[0] == CanonicalMatchStatus.MISMATCH


def test_request_names_are_matched_literally_not_as_patterns():
    m = live_map(**{"a.c": "1", "spironolactone": "9997"})
    assert extract_claim_identity("abc interacts with spironolactone", m) is None


# ── Phase C / Scenario 7: candidate isolation ────────────────────────────────


def test_the_production_resolver_loads_no_pending_record():
    store = live_relationships.load_relationship_store([], directory=str(REL_DIR))
    assert all(r.record_id != "REL-LIVE-0003" for r in store.records)
    assert store.between(["29046", "9997"]) == []
    assert store.evidence == ()


# ── Phase D: malformed provider responses ────────────────────────────────────

class Resp:
    def __init__(self, status, body=None, raise_json=False, text=""):
        self.status_code, self._body, self._raise, self.text, self.headers = status, body, raise_json, text, {}

    def json(self):
        if self._raise:
            raise json.JSONDecodeError("Expecting value", "<html>", 0)
        return self._body


def llm_call(resp):
    b = OpenAICompatibleBackend("groq", "https://example.invalid/v1", FAKE_KEY, "m")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as post:
        post.return_value = resp
        return asyncio.run(b.generate_structured("p", {"type": "json_object"}))


@pytest.mark.parametrize("resp", [
    Resp(200, raise_json=True),                                 # HTML or truncated body
    Resp(200, body=["not", "an", "object"]),
    Resp(200, body={"choices": [{"message": None}]}),
    Resp(200, body={"choices": [{"message": {"content": None}}]}),
    Resp(200, body={"choices": ["text"]}),
])
def test_a_malformed_200_is_a_schema_error_not_a_raw_exception(resp):
    with pytest.raises(ModelExecutionError) as exc:
        llm_call(resp)
    assert exc.value.failure_class == FailureClass.SCHEMA_ERROR
    assert exc.value.status_code == "MALFORMED_RESPONSE"
    assert FAKE_KEY not in str(exc.value)


# A synthetic "echoed prompt": what an upstream error body could carry back.
SENTINEL = "SENTINEL-ECHO-7f3a synthetic prompt text Warfarin 5 mg"


@pytest.mark.parametrize("status, text, failure_class", [
    (400, json.dumps({"error": {"code": "json_validate_failed", "message": SENTINEL}}), FailureClass.SCHEMA_ERROR),
    (503, f"upstream overloaded while processing: {SENTINEL}", FailureClass.TRANSIENT_PROVIDER),
    (401, f"invalid key {FAKE_KEY} for request {SENTINEL}", FailureClass.AUTHENTICATION),
])
def test_an_upstream_error_body_is_classified_but_never_logged(caplog, status, text, failure_class):
    with caplog.at_level(logging.DEBUG, logger="adaptive_trust_medical_rag"):
        with pytest.raises(ModelExecutionError) as exc:
            llm_call(Resp(status, text=text))
    assert exc.value.failure_class == failure_class  # the body still drives the classification
    assert SENTINEL not in caplog.text and FAKE_KEY not in caplog.text and SENTINEL not in str(exc.value)
    assert f"groq HTTP {status}" in caplog.text  # who failed, and how, is still logged


def test_a_valid_completion_is_unchanged():
    out = llm_call(Resp(200, body={"id": "x", "choices": [{"message": {"content": "{\"a\": 1}"},
                                                            "finish_reason": "stop"}]}))
    assert out.content == "{\"a\": 1}" and out.structured_output == {"a": 1} and out.finish_reason == "stop"


def test_the_router_fails_over_on_a_malformed_response_and_records_the_attempt():
    bad = OpenAICompatibleBackend("groq", "https://example.invalid/v1", FAKE_KEY, "groq-m")
    good = SimpleNamespace(
        get_model_metadata=lambda: {"provider": "nvidia", "model": "nvidia-m"},
        generate_structured=AsyncMock(return_value=SimpleNamespace(provider="nvidia", model="nvidia-m",
                                                                   content="{}", attempts=None)))
    r = LiveProviderRouter(provider_priority=["groq", "nvidia"], deadline_s=10.0)
    r.register_provider("groq", bad)
    r.register_provider("nvidia", good)
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as post:
        post.return_value = Resp(200, raise_json=True)
        out = asyncio.run(r.generate_structured("p", {"type": "json_object"}))
    assert out.provider == "nvidia"
    assert [(a["provider"], a["outcome"], a.get("failure_class")) for a in out.attempts] == [
        ("groq", "failed", "SCHEMA_ERROR"), ("nvidia", "success", None)]


# ── Phase E: vision model attribution and malformed output ───────────────────

GOOD_VISION = {"choices": [{"message": {"content": json.dumps({
    "raw_text": "SYNTHETIC", "warnings": [],
    "candidate_medications": [{"raw_text": "DrugA", "normalized_text": "druga", "confidence": "HIGH"}]})}}]}


def vision_backend(fallback=None):
    return OpenAIVisionBackend(base_url="https://example.invalid/v1", api_key=FAKE_KEY,
                               model_name="vision-primary", timeout_s=5.0, fallback_model=fallback)


def test_the_extraction_names_the_model_that_produced_it():
    b = vision_backend("vision-fallback")
    # A timeout is not retried on the same model, so one stall moves the request to the fallback.
    responses = iter([httpx.ReadTimeout("slow"), Resp(200, body=GOOD_VISION)])

    async def post(self, url, json=None, headers=None):
        r = next(responses)
        if isinstance(r, Exception):
            raise r
        return r

    with patch("httpx.AsyncClient.post", new=post):
        result = asyncio.run(b.extract_medications(b"\x89PNG", "image/png"))
    assert result.model_used == "vision-fallback"


def test_concurrent_extractions_each_keep_their_own_model():
    """One request on the primary, one moved to the fallback: neither reports the other's model."""
    b = vision_backend("vision-fallback")
    gate = asyncio.Event()

    async def post(self, url, json=None, headers=None):
        model = json["model"]
        if model == "vision-primary" and json["messages"][-1]["content"][-1]["image_url"]["url"].endswith("QQ=="):
            raise httpx.ReadTimeout("slow")       # request B's primary times out
        if model == "vision-primary":
            await gate.wait()                     # request A finishes last, after B used the fallback
        return Resp(200, body=GOOD_VISION)

    async def run():
        async def b_then_open():
            res = await b.extract_medications(b"A", "image/png")   # base64 "QQ=="
            gate.set()
            return res
        return await asyncio.gather(b.extract_medications(b"\x89PNG", "image/png"), b_then_open())

    with patch("httpx.AsyncClient.post", new=post):
        a, bb = asyncio.run(run())
    assert a.model_used == "vision-primary"
    assert bb.model_used == "vision-fallback"


def test_a_malformed_vision_200_is_a_schema_error_with_no_medications():
    b = vision_backend()
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as post:
        post.return_value = Resp(200, raise_json=True)
        with pytest.raises(ModelExecutionError) as exc:
            asyncio.run(b.extract_medications(b"\x89PNG", "image/png"))
    assert exc.value.failure_class == FailureClass.SCHEMA_ERROR


# ── Phase D: provider settings the live router ignores ───────────────────────

LLM_ENV = ("LLM_PROVIDER", "LLM_PRIMARY_PROVIDER", "LLM_FALLBACK_PROVIDERS", "LLM_FALLBACK_PROVIDER",
           "LLM_FAILOVER_ENABLED", "GROQ_API_KEY", "GROQ_MODEL", "NVIDIA_LLM_API_KEY", "NVIDIA_API_KEY",
           "NVIDIA_LLM_MODEL", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID", "CLOUDFLARE_ENABLED",
           "LLM_REQUEST_DEADLINE_S")


@pytest.fixture
def clean_env(monkeypatch):
    for k in LLM_ENV:
        monkeypatch.delenv(k, raising=False)
    return monkeypatch


def test_an_unread_singular_fallback_setting_is_reported_and_changes_nothing(clean_env, caplog):
    clean_env.setenv("LLM_PROVIDER", "groq")
    clean_env.setenv("GROQ_API_KEY", FAKE_KEY)
    clean_env.setenv("NVIDIA_API_KEY", FAKE_KEY)
    _, before = app_module.build_llm_router()
    clean_env.setenv("LLM_FALLBACK_PROVIDER", "gemini")
    with caplog.at_level(logging.WARNING):
        _, after = app_module.build_llm_router()
    assert after["order"] == before["order"]
    assert "LLM_FALLBACK_PROVIDER=gemini is not read" in caplog.text
    assert "names 'gemini', which the live application has no adapter for" in caplog.text
    assert FAKE_KEY not in caplog.text


def test_cloudflare_enabled_false_is_reported_when_its_credentials_still_register_it(clean_env, caplog):
    clean_env.setenv("CLOUDFLARE_API_TOKEN", FAKE_KEY)
    clean_env.setenv("CLOUDFLARE_ACCOUNT_ID", "acct")
    clean_env.setenv("CLOUDFLARE_ENABLED", "false")
    with caplog.at_level(logging.WARNING):
        _, config = app_module.build_llm_router()
    assert [p["provider"] for p in config["order"]] == ["cloudflare"]
    assert "CLOUDFLARE_ENABLED=false is not read" in caplog.text


def test_supported_settings_raise_no_warning(clean_env, caplog):
    clean_env.setenv("GROQ_API_KEY", FAKE_KEY)
    clean_env.setenv("LLM_FALLBACK_PROVIDERS", "nvidia")
    with caplog.at_level(logging.WARNING):
        app_module.build_llm_router()
    assert "is not read" not in caplog.text and "no adapter" not in caplog.text


# ── Provenance label ─────────────────────────────────────────────────────────

def cand(text, content_hash):
    prov = {"source": "DAILYMED", "content_hash": content_hash} if content_hash is not None else {"source": "DAILYMED"}
    return Candidate(chunk_id="c", document_id="d", text=text, metadata={"provenance": prov})


def test_provenance_status_comes_from_the_registered_hash():
    text = "Synthetic evidence."
    assert _provenance_status(cand(text, hashlib.sha256(text.encode()).hexdigest())) == "CONTENT_HASH_MATCHED"
    assert _provenance_status(cand(text, "0" * 64)) == "CONTENT_HASH_MISMATCH"
    assert _provenance_status(cand(text, None)) == "NO_REGISTERED_HASH"


# ── Vision reply parsing (2026-10-22 browser failure: "malformed JSON object") ─

from adaptive_trust_medical_rag.llm_backend.openai_vision_backend import (
    _parse_and_validate_vision_response,  # noqa: E402
)


def test_a_transcription_with_literal_line_breaks_inside_a_string_is_parsed():
    reply = ('{"raw_text": "SYNTHETIC CLINIC\\nRx\nLisinopril 10 mg\tdaily", "warnings": [], '
             '"candidate_medications": [{"raw_text": "Lisinopril 10 mg", "normalized_text": "lisinopril", '
             '"confidence": "HIGH"}]}')
    parsed = _parse_and_validate_vision_response(reply)
    assert parsed["candidate_medications"][0]["normalized_text"] == "lisinopril"


@pytest.mark.parametrize("reply", [
    '{"raw_text": "x", "candidate_medications": [{"raw_text": "DrugA", "confidence": "HIGH"},], "warnings": []}',
    "{'raw_text': 'x', 'candidate_medications': []}",
    '{"raw_text": "x"} {"candidate_medications": []}',
])
def test_structurally_invalid_json_still_fails_closed_with_the_reason_but_not_the_content(reply):
    with pytest.raises(ModelExecutionError) as exc:
        _parse_and_validate_vision_response(reply)
    msg = str(exc.value)
    assert exc.value.failure_class == FailureClass.SCHEMA_ERROR
    assert msg.startswith("Vision provider returned malformed JSON object (") and "line 1, column" in msg
    assert "DrugA" not in msg
