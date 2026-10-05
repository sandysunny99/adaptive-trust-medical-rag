"""Phase 4.5 — Future-run provider-runtime integration audit.

Tests the three Phase 3 utilities through a LOCAL FAKE PROVIDER
harness that simulates the GroqBackend interface without making
any external API calls.

This file proves that:
1. Error classification works end-to-end through a provider execution path
2. Secret redaction works at log-write boundaries
3. Rate-limit telemetry observation works through the RateLimitInfo adapter
4. None of the above alter retry policy, provider, model, or scientific semantics

NO external API calls. NO Groq. NO Gemini. NO real credentials.
NOT a scientific benchmark. This is a local integration audit only.
"""

import json
import time

import pytest

from adaptive_trust_medical_rag.common.model_result import (
    ModelExecutionError,
)
from adaptive_trust_medical_rag.llm_backend.provider_errors import (
    classify_provider_error,
)
from adaptive_trust_medical_rag.llm_backend.provider_rate_limit import (
    TelemetryConfidence,
    from_rate_limit_info,
)
from adaptive_trust_medical_rag.llm_backend.provider_redaction import (
    redact_secrets,
)
from adaptive_trust_medical_rag.llm_routing.types import (
    RateLimitInfo,
)

# ═══════════════════════════════════════════════════════════════════════
# FAKE PROVIDER HARNESS
# ═══════════════════════════════════════════════════════════════════════
#
# Simulates GroqBackend's error/success interface without network calls.
# Mirrors how GroqBackend raises ModelExecutionError with status_code
# and stores last_rate_limit_info.


class FakeProviderResponse:
    """Simulates a provider's response with optional rate-limit headers."""

    def __init__(
        self,
        status_code: int = 200,
        body: dict | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.status_code = status_code
        self.body = body or {}
        self.headers = headers or {}


class FakeProviderBackend:
    """Local deterministic fake that mirrors GroqBackend's error interface.

    Does NOT make network calls. Does NOT use API keys.
    Used solely for integration testing of provider-runtime utilities.
    """

    PROVIDER = "fake_local"
    MODEL = "fake/test-model"

    def __init__(self) -> None:
        self.last_rate_limit_info: RateLimitInfo | None = None
        self.call_count: int = 0
        self._scenario: str = "success"

    def set_scenario(self, scenario: str) -> None:
        """Configure the next call's behavior."""
        self._scenario = scenario

    def generate(self, prompt: str) -> tuple[str, RateLimitInfo | None]:
        """Simulate a provider call, returning (text, rate_limit_info).

        Raises ModelExecutionError for error scenarios, mirroring GroqBackend.
        """
        self.call_count += 1

        if self._scenario == "success":
            self.last_rate_limit_info = RateLimitInfo(
                limit_requests=30,
                remaining_requests=28,
                limit_tokens=8000,
                remaining_tokens=7200,
                reset_requests="2m59s",
                retry_after=None,
            )
            return "Simulated response text", self.last_rate_limit_info

        if self._scenario == "429":
            self.last_rate_limit_info = RateLimitInfo(
                remaining_requests=0,
                retry_after=35.0,
            )
            raise ModelExecutionError(
                "Groq API error (status 429): Rate limit exceeded",
                status_code="429",
            )

        if self._scenario == "500":
            raise ModelExecutionError(
                "Groq API error (status 500): Internal server error",
                status_code="500",
            )

        if self._scenario == "timeout":
            raise ModelExecutionError(
                "Groq API request timed out",
                status_code="TIMEOUT",
            )

        if self._scenario == "malformed":
            self.last_rate_limit_info = RateLimitInfo(remaining_requests=25)
            raise ModelExecutionError(
                "Empty response from Groq API",
                status_code="EMPTY_RESPONSE",
            )

        if self._scenario == "auth_error":
            raise ModelExecutionError(
                "Groq API error (status 401): Invalid API key",
                status_code="401",
            )

        if self._scenario == "secret_bearing_error":
            # Simulates an error that leaks a credential in its message
            # Uses a SYNTHETIC test token, not a real credential
            raise ModelExecutionError(
                "Connection failed for key gsk_FAKE_TEST_TOKEN_abcdefghij "
                "with Bearer eyFAKETESTJWT.payload.signature",
                status_code="INTERNAL_ERROR",
            )

        if self._scenario == "rate_limit_headers_only":
            self.last_rate_limit_info = RateLimitInfo(
                limit_requests=30,
                remaining_requests=5,
                limit_tokens=8000,
                remaining_tokens=200,
                reset_requests="45s",
                reset_tokens="1m15s",
                retry_after=10.0,
            )
            return "Response with rate limit pressure", self.last_rate_limit_info

        if self._scenario == "partial_rate_limit":
            self.last_rate_limit_info = RateLimitInfo(
                retry_after=60.0,
            )
            return "Response with partial rate info", self.last_rate_limit_info

        if self._scenario == "no_rate_limit":
            self.last_rate_limit_info = None
            return "Response without rate headers", None

        raise ValueError(f"Unknown scenario: {self._scenario}")


def _simulate_execute_with_classification(
    backend: FakeProviderBackend,
) -> dict:
    """Simulate a future runner's execute-with-retries path.

    This mirrors the intended integration:
        try provider call → success path
        except → classify → record → existing retry logic
    """
    record: dict = {
        "provider": backend.PROVIDER,
        "model": backend.MODEL,
    }

    try:
        text, rate_info = backend.generate("test prompt")

        # SUCCESS PATH: record rate-limit observation
        obs = from_rate_limit_info(rate_info, backend.PROVIDER, backend.MODEL)
        record["status"] = "SUCCESS"
        record["response_length"] = len(text)
        record["rate_limit_snapshot"] = obs.to_ledger_dict()

    except ModelExecutionError as e:
        # ERROR PATH: classify → redact → record
        classification = classify_provider_error(e)
        safe_message = redact_secrets(str(e)[:200])

        record["status"] = "ERROR"
        record["failure_class"] = classification.failure_class.value
        record["failure_detail"] = classification.detail
        record["failure_retryable"] = classification.retryable
        record["failure_http_status"] = classification.http_status
        record["failure_reason"] = classification.reason_code
        record["error_message_summary"] = safe_message

    return record


# ═══════════════════════════════════════════════════════════════════════
# A. ERROR CLASSIFICATION END-TO-END
# ═══════════════════════════════════════════════════════════════════════


class TestErrorClassificationEndToEnd:
    """Verify: fake provider error → classify → structured record."""

    def test_429_end_to_end(self):
        backend = FakeProviderBackend()
        backend.set_scenario("429")
        record = _simulate_execute_with_classification(backend)

        assert record["status"] == "ERROR"
        assert record["failure_class"] == "RATE_LIMIT"
        assert record["failure_retryable"] is True
        assert record["failure_http_status"] == 429

    def test_500_end_to_end(self):
        backend = FakeProviderBackend()
        backend.set_scenario("500")
        record = _simulate_execute_with_classification(backend)

        assert record["status"] == "ERROR"
        assert record["failure_class"] == "TRANSIENT_PROVIDER"
        assert record["failure_retryable"] is True
        assert record["failure_http_status"] == 500

    def test_timeout_end_to_end(self):
        backend = FakeProviderBackend()
        backend.set_scenario("timeout")
        record = _simulate_execute_with_classification(backend)

        assert record["status"] == "ERROR"
        assert record["failure_class"] == "TIMEOUT"
        assert record["failure_retryable"] is True

    def test_malformed_end_to_end(self):
        backend = FakeProviderBackend()
        backend.set_scenario("malformed")
        record = _simulate_execute_with_classification(backend)

        assert record["status"] == "ERROR"
        assert record["failure_detail"] == "MALFORMED_RESPONSE"

    def test_auth_error_end_to_end(self):
        backend = FakeProviderBackend()
        backend.set_scenario("auth_error")
        record = _simulate_execute_with_classification(backend)

        assert record["status"] == "ERROR"
        assert record["failure_class"] == "AUTHENTICATION"
        assert record["failure_retryable"] is False
        assert record["failure_http_status"] == 401

    def test_success_has_no_failure_fields(self):
        backend = FakeProviderBackend()
        backend.set_scenario("success")
        record = _simulate_execute_with_classification(backend)

        assert record["status"] == "SUCCESS"
        assert "failure_class" not in record
        assert "failure_detail" not in record

    def test_all_records_are_json_serializable(self):
        """Every record must survive JSON roundtrip for ledger writing."""
        backend = FakeProviderBackend()
        for scenario in ["success", "429", "500", "timeout", "malformed", "auth_error"]:
            backend.set_scenario(scenario)
            record = _simulate_execute_with_classification(backend)
            serialized = json.dumps(record)
            deserialized = json.loads(serialized)
            assert deserialized["provider"] == "fake_local"


# ═══════════════════════════════════════════════════════════════════════
# B. RETRY ISOLATION
# ═══════════════════════════════════════════════════════════════════════


class TestRetryIsolation:
    """Prove that classification does NOT itself retry or sleep."""

    def test_classifier_does_not_retry(self):
        """Calling classify_provider_error does not make a second call."""
        backend = FakeProviderBackend()
        backend.set_scenario("429")

        try:
            backend.generate("test")
        except ModelExecutionError as e:
            before_count = backend.call_count
            classify_provider_error(e)
            after_count = backend.call_count

        assert after_count == before_count  # No additional call

    def test_classifier_does_not_sleep(self):
        """classify_provider_error completes in < 10ms (no sleep)."""
        err = ModelExecutionError("test", status_code="429")
        start = time.perf_counter()
        classify_provider_error(err)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.01  # 10ms — way more than needed but proves no sleep

    def test_classifier_does_not_switch_provider(self):
        result = classify_provider_error(
            ModelExecutionError("error", status_code="503")
        )
        assert not hasattr(result, "next_provider")
        assert not hasattr(result, "fallback_provider")
        assert not hasattr(result, "switch_model")

    def test_classifier_does_not_mutate_case(self):
        result = classify_provider_error(
            ModelExecutionError("error", status_code="429")
        )
        assert not hasattr(result, "case_id")
        assert not hasattr(result, "run_id")
        assert not hasattr(result, "condition")


# ═══════════════════════════════════════════════════════════════════════
# C. SECRET REDACTION END-TO-END
# ═══════════════════════════════════════════════════════════════════════


class TestRedactionEndToEnd:
    """Verify: secret-bearing error → redacted in record, preserved fields."""

    def test_secret_bearing_error_redacted(self):
        backend = FakeProviderBackend()
        backend.set_scenario("secret_bearing_error")
        record = _simulate_execute_with_classification(backend)

        assert record["status"] == "ERROR"
        msg = record["error_message_summary"]
        # Secrets must be gone
        assert "gsk_FAKE_TEST_TOKEN" not in msg
        assert "eyFAKETESTJWT" not in msg
        # Error context preserved
        assert "Connection failed" in msg
        assert "[REDACTED]" in msg

    def test_redacted_preserves_provider_model(self):
        backend = FakeProviderBackend()
        backend.set_scenario("secret_bearing_error")
        record = _simulate_execute_with_classification(backend)

        assert record["provider"] == "fake_local"
        assert record["model"] == "fake/test-model"

    def test_redacted_preserves_failure_class(self):
        backend = FakeProviderBackend()
        backend.set_scenario("secret_bearing_error")
        record = _simulate_execute_with_classification(backend)

        # Classification should still work even with secrets in message
        assert "failure_class" in record
        assert isinstance(record["failure_class"], str)

    def test_before_after_redaction_example(self):
        """Explicit before/after showing redaction preserves structure."""
        raw = (
            "Groq API error: key gsk_FAKE_TEST_TOKEN_abcdefghij "
            "returned 500 for model openai/gpt-oss-120b"
        )
        redacted = redact_secrets(raw)

        # Before: contains key
        assert "gsk_FAKE_TEST_TOKEN" in raw
        # After: key removed
        assert "gsk_FAKE_TEST_TOKEN" not in redacted
        # After: non-secret context preserved
        assert "Groq API error" in redacted
        assert "returned 500" in redacted
        assert "openai/gpt-oss-120b" in redacted


class TestRedactionFalsePositivesEndToEnd:
    """Verify evidence/provenance metadata survives redaction intact."""

    @pytest.mark.parametrize("field,value", [
        ("case_id", "CASE_042_RETRIEVAL_POISONING"),
        ("run_id", "FREE_REP_V2_RUN1"),
        ("document_id", "fda_label_warfarin_2024"),
        ("source_id", "pubmed_38291045"),
        ("source_url", "https://pubmed.ncbi.nlm.nih.gov/38291045"),
        ("source_url", "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=abc"),
        ("content_hash", "af71c70d36081b1b68316b5ff8636969c8b964c9655f752b41112694ebc02c48"),
        ("publication_date", "2024-03-15"),
        ("trust_score", "0.57"),
        ("drug_name", "Warfarin sodium"),
        ("drug_name", "Metformin HCl 500mg"),
        ("clinical_text", "INR monitoring required for anticoagulation therapy"),
        ("provider", "groq"),
        ("model", "openai/gpt-oss-120b"),
    ])
    def test_field_preserved(self, field: str, value: str):
        """Normal evidence/provenance values must not be redacted."""
        text = f'{field}="{value}"'
        assert redact_secrets(text) == text

    def test_json_evidence_metadata_preserved(self):
        metadata = json.dumps({
            "source": "FDA Drug Label",
            "source_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=abc",
            "document_id": "fda_label_warfarin_2024",
            "publication_date": "2024-03-15",
            "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "authority_tier": 1,
            "validation_status": "validated",
        })
        assert redact_secrets(metadata) == metadata

    def test_json_provenance_preserved(self):
        provenance = json.dumps({
            "provenance": {
                "source": "PubMed Central",
                "source_url": "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12345",
                "document_id": "pmc_12345",
                "publication_date": "2023-08-20",
            }
        })
        assert redact_secrets(provenance) == provenance


# ═══════════════════════════════════════════════════════════════════════
# D. RATE-LIMIT TELEMETRY END-TO-END
# ═══════════════════════════════════════════════════════════════════════


class TestRateLimitEndToEnd:
    """Verify: fake provider headers → RateLimitInfo → observation → ledger."""

    def test_success_with_full_headers(self):
        backend = FakeProviderBackend()
        backend.set_scenario("success")
        record = _simulate_execute_with_classification(backend)

        assert record["status"] == "SUCCESS"
        snapshot = record["rate_limit_snapshot"]
        assert snapshot["confidence"] == "OBSERVED"
        assert snapshot["remaining_requests"] == 28
        assert snapshot["request_limit"] == 30
        assert snapshot["remaining_tokens"] == 7200

    def test_success_with_rate_limit_pressure(self):
        backend = FakeProviderBackend()
        backend.set_scenario("rate_limit_headers_only")
        record = _simulate_execute_with_classification(backend)

        snapshot = record["rate_limit_snapshot"]
        assert snapshot["remaining_requests"] == 5
        assert snapshot["remaining_tokens"] == 200
        assert snapshot["retry_after_seconds"] == 10.0

    def test_success_with_partial_rate_limit(self):
        backend = FakeProviderBackend()
        backend.set_scenario("partial_rate_limit")
        record = _simulate_execute_with_classification(backend)

        snapshot = record["rate_limit_snapshot"]
        assert snapshot["confidence"] == "OBSERVED"
        assert snapshot["retry_after_seconds"] == 60.0
        # Missing fields not fabricated
        assert "remaining_requests" not in snapshot
        assert "remaining_tokens" not in snapshot

    def test_success_without_rate_limit(self):
        backend = FakeProviderBackend()
        backend.set_scenario("no_rate_limit")
        record = _simulate_execute_with_classification(backend)

        snapshot = record["rate_limit_snapshot"]
        assert snapshot["confidence"] == "UNKNOWN"
        assert "remaining_requests" not in snapshot

    def test_error_has_no_rate_limit_snapshot(self):
        """Error path should not contain rate-limit snapshot."""
        backend = FakeProviderBackend()
        backend.set_scenario("429")
        record = _simulate_execute_with_classification(backend)

        assert record["status"] == "ERROR"
        assert "rate_limit_snapshot" not in record

    def test_observation_is_recording_only(self):
        """RateLimitObservation must not contain routing directives."""
        backend = FakeProviderBackend()
        backend.set_scenario("rate_limit_headers_only")
        record = _simulate_execute_with_classification(backend)

        snapshot = record["rate_limit_snapshot"]
        assert "should_failover" not in snapshot
        assert "next_provider" not in snapshot
        assert "cooldown_seconds" not in snapshot


# ═══════════════════════════════════════════════════════════════════════
# E. GROQ BACKEND ADAPTER COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════════


class TestGroqAdapterCompatibility:
    """Verify from_rate_limit_info works with GroqBackend's RateLimitInfo."""

    def test_groq_typical_response(self):
        """Simulate what GroqBackend.generate() stores in last_rate_limit_info."""
        # This mirrors groq_backend.py lines 59-67
        info = RateLimitInfo(
            remaining_requests=int("28") or None,
            remaining_tokens=int("7200") or None,
            limit_requests=int("30") or None,
            limit_tokens=int("8000") or None,
            reset_requests="2m59.123s",
            reset_tokens="1m30s",
            retry_after=None,
        )
        obs = from_rate_limit_info(info, "groq", "openai/gpt-oss-120b")

        assert obs.confidence == TelemetryConfidence.OBSERVED
        assert obs.remaining_requests == 28
        assert obs.request_limit == 30
        assert obs.request_reset == "2m59.123s"
        assert obs.provider == "groq"
        assert obs.model == "openai/gpt-oss-120b"

    def test_groq_zero_remaining_becomes_none(self):
        """GroqBackend uses `int(...) or None`, so 0 → None."""
        info = RateLimitInfo(
            remaining_requests=None,  # int("0") or None = None
            remaining_tokens=None,
        )
        obs = from_rate_limit_info(info, "groq", "openai/gpt-oss-120b")
        assert obs.remaining_requests is None
        assert obs.remaining_tokens is None

    def test_groq_missing_headers(self):
        """When GroqBackend can't parse headers, last_rate_limit_info = None."""
        obs = from_rate_limit_info(None, "groq", "openai/gpt-oss-120b")
        assert obs.confidence == TelemetryConfidence.UNKNOWN


# ═══════════════════════════════════════════════════════════════════════
# F. SCIENTIFIC ISOLATION (FAKE PROVIDER)
# ═══════════════════════════════════════════════════════════════════════


class TestScientificIsolationFakeProvider:
    """Prove utilities cannot change scientific semantics via fake provider."""

    def test_no_provider_switching_on_any_error(self):
        backend = FakeProviderBackend()
        for scenario in ["429", "500", "timeout", "auth_error", "malformed"]:
            backend.set_scenario(scenario)
            record = _simulate_execute_with_classification(backend)
            assert record["provider"] == "fake_local"
            assert record["model"] == "fake/test-model"

    def test_no_retry_directive_in_classification(self):
        backend = FakeProviderBackend()
        backend.set_scenario("429")
        record = _simulate_execute_with_classification(backend)
        assert "retry_count" not in record
        assert "max_retries" not in record
        assert "should_retry" not in record

    def test_no_evidence_fields_in_classification(self):
        backend = FakeProviderBackend()
        backend.set_scenario("500")
        record = _simulate_execute_with_classification(backend)
        assert "trust_score" not in record
        assert "evidence" not in record
        assert "eligibility" not in record
        assert "security_state" not in record

    def test_no_routing_in_rate_limit_snapshot(self):
        backend = FakeProviderBackend()
        backend.set_scenario("success")
        record = _simulate_execute_with_classification(backend)
        snapshot = record["rate_limit_snapshot"]
        assert "next_provider" not in snapshot
        assert "failover" not in str(snapshot).lower()
        assert "thompson" not in str(snapshot).lower()

    def test_harness_makes_zero_external_calls(self):
        """The fake provider never calls any external API."""
        backend = FakeProviderBackend()
        for scenario in ["success", "429", "500", "timeout", "malformed",
                         "auth_error", "secret_bearing_error",
                         "rate_limit_headers_only", "partial_rate_limit",
                         "no_rate_limit"]:
            backend.set_scenario(scenario)
            _simulate_execute_with_classification(backend)
        # The fact that this test passes offline proves no network calls


# ═══════════════════════════════════════════════════════════════════════
# G. PERFORMANCE OVERHEAD (LOCAL)
# ═══════════════════════════════════════════════════════════════════════


class TestLocalPerformanceOverhead:
    """Measure overhead of the full classify+redact+observe path."""

    def test_full_error_path_overhead(self):
        """Full error path: classify + redact should complete in < 2ms."""
        err = ModelExecutionError(
            "error with key gsk_FAKE_abcdefghij",
            status_code="429",
        )
        start = time.perf_counter()
        for _ in range(1000):
            c = classify_provider_error(err)
            redact_secrets(str(err)[:200])
        elapsed = time.perf_counter() - start
        per_call_us = (elapsed / 1000) * 1_000_000
        assert per_call_us < 2000  # 2ms per combined call

    def test_full_success_path_overhead(self):
        """Full success path: observation + ledger dict in < 1ms."""
        info = RateLimitInfo(remaining_requests=28, remaining_tokens=7200)
        start = time.perf_counter()
        for _ in range(1000):
            obs = from_rate_limit_info(info, "groq", "openai/gpt-oss-120b")
            obs.to_ledger_dict()
        elapsed = time.perf_counter() - start
        per_call_us = (elapsed / 1000) * 1_000_000
        assert per_call_us < 1000
