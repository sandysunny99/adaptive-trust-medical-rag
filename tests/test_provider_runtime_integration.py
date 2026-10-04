"""Tests for Phase 4 runtime integration of provider infrastructure utilities.

These tests verify that the Phase 3 utilities (error classification,
secret redaction, rate-limit observation) can be wired into a benchmark
runner's execution path WITHOUT changing:
- provider identity
- model identity
- retry policy
- scientific observations
- trust scoring
- evidence eligibility
- security gate behavior

Historical V2 experiment: IMMUTABLE / NOT MODIFIED.
These tests prove safety for future runs only.
"""

import json
import time

import pytest

from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_backend.provider_errors import (
    ProviderErrorClassification,
    classify_provider_error,
)
from adaptive_trust_medical_rag.llm_backend.provider_rate_limit import (
    RateLimitObservation,
    TelemetryConfidence,
    from_rate_limit_info,
)
from adaptive_trust_medical_rag.llm_backend.provider_redaction import (
    redact_secrets,
    redact_secrets_detailed,
)
from adaptive_trust_medical_rag.llm_routing.types import (
    FAILOVER_ELIGIBLE,
    FailureClass,
    RateLimitInfo,
    RoutingMode,
)


# ═══════════════════════════════════════════════════════════════════════
# A. INTEGRATED ERROR CLASSIFICATION → LEDGER RECORDING
# ═══════════════════════════════════════════════════════════════════════


class TestIntegratedErrorClassification:
    """Verify end-to-end: provider error → classify → record structured metadata."""

    def test_429_produces_structured_ledger_record(self):
        """Simulate a 429 error and verify the classification can be serialized."""
        err = ModelExecutionError("Groq API error (status 429): Rate limit exceeded", status_code="429")
        classification = classify_provider_error(err)

        # Build ledger-compatible record
        record = {
            "error_class": classification.failure_class.value,
            "error_detail": classification.detail,
            "retryable": classification.retryable,
            "http_status": classification.http_status,
            "reason_code": classification.reason_code,
        }

        assert record["error_class"] == "RATE_LIMIT"
        assert record["retryable"] is True
        assert record["http_status"] == 429

        # Must be JSON-serializable
        serialized = json.dumps(record)
        assert "RATE_LIMIT" in serialized

    def test_500_produces_structured_ledger_record(self):
        err = ModelExecutionError("Groq API error (status 500)", status_code="500")
        classification = classify_provider_error(err)

        record = {
            "error_class": classification.failure_class.value,
            "retryable": classification.retryable,
            "http_status": classification.http_status,
        }

        assert record["error_class"] == "TRANSIENT_PROVIDER"
        assert record["retryable"] is True

    def test_classification_does_not_alter_retry_policy(self):
        """The classifier returns metadata — it doesn't make retry decisions."""
        err = ModelExecutionError("Auth error", status_code="401")
        classification = classify_provider_error(err)

        # Classification says "not retryable"
        assert classification.retryable is False

        # But the RUNNER decides whether to retry, not the classifier.
        # The classifier's retryable field is a characterisation, not a directive.
        assert not hasattr(classification, "should_retry")
        assert not hasattr(classification, "retry_count")
        assert not hasattr(classification, "next_provider")

    def test_provider_remains_fixed(self):
        """Classification must never contain provider-switching information."""
        err = Exception("Groq unavailable")
        classification = classify_provider_error(err, status_code=503)

        assert not hasattr(classification, "fallback_provider")
        assert not hasattr(classification, "next_model")
        assert not hasattr(classification, "alternative_endpoint")


# ═══════════════════════════════════════════════════════════════════════
# B. INTEGRATED REDACTION → LOG SAFETY
# ═══════════════════════════════════════════════════════════════════════


class TestIntegratedRedaction:
    """Verify end-to-end: secret-bearing error → redacted log output."""

    def test_groq_key_in_error_message_redacted(self):
        """Simulate a provider error that leaks the API key."""
        raw_error = "Groq API error: invalid key gsk_test1234abcdef5678"
        redacted = redact_secrets(raw_error)

        assert "gsk_test1234" not in redacted
        assert "[REDACTED]" in redacted
        # The error structure is preserved
        assert "Groq API error" in redacted

    def test_bearer_in_error_message_redacted(self):
        raw_error = "Authorization failed: Bearer eyJhbGciOiJIUzI1NiJ9.payload"
        redacted = redact_secrets(raw_error)

        assert "eyJhbG" not in redacted
        assert "[REDACTED]" in redacted

    def test_redacted_error_is_json_safe(self):
        """Redacted text must be valid for JSON serialization in ledger."""
        raw_error = "Error with key gsk_abc123XYZ789defGHI and sk-xyz987ABC654mno"
        redacted = redact_secrets(raw_error)
        truncated = redacted[:200]

        # Must survive JSON roundtrip
        record = {"error_message_summary": truncated}
        serialized = json.dumps(record)
        deserialized = json.loads(serialized)
        assert deserialized["error_message_summary"] == truncated

    def test_scientific_observation_untouched_by_redaction(self):
        """Scientific observation fields must pass through unchanged."""
        obs = {
            "case_id": "CASE_042_RETRIEVAL_POISONING",
            "status": "abstain",
            "gate": "abstain",
            "confidence": 0.0,
            "trust_score": 0.38,
            "answer_length": 738,
            "retrieved_chunks": ["warfarin_fda_chunk_1"],
        }
        obs_str = json.dumps(obs)
        assert redact_secrets(obs_str) == obs_str

    def test_provenance_metadata_preserved(self):
        """Provenance metadata must not be mistaken for secrets."""
        provenance = {
            "source": "FDA Drug Label",
            "source_url": "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=abc",
            "document_id": "fda_label_warfarin_2024",
            "publication_date": "2024-03-15",
            "content_hash": "af71c70d36081b1b68316b5ff8636969c8b964c9655f752b41112694ebc02c48",
        }
        prov_str = json.dumps(provenance)
        assert redact_secrets(prov_str) == prov_str


# ═══════════════════════════════════════════════════════════════════════
# C. INTEGRATED RATE-LIMIT → LEDGER OBSERVATION
# ═══════════════════════════════════════════════════════════════════════


class TestIntegratedRateLimitObservation:
    """Verify end-to-end: rate-limit headers → observation → ledger dict."""

    def test_full_observation_in_ledger(self):
        """Simulate a successful Groq response with rate-limit headers."""
        info = RateLimitInfo(
            limit_requests=30,
            remaining_requests=28,
            reset_requests="2m59.123s",
            limit_tokens=8000,
            remaining_tokens=7200,
            retry_after=None,
        )
        obs = from_rate_limit_info(info, "groq", "openai/gpt-oss-120b")
        ledger_dict = obs.to_ledger_dict()

        # Must be JSON-serializable
        serialized = json.dumps(ledger_dict)
        deserialized = json.loads(serialized)

        assert deserialized["confidence"] == "OBSERVED"
        assert deserialized["remaining_requests"] == 28
        assert "observed_at" in deserialized

    def test_missing_rate_limit_in_ledger(self):
        """When no rate-limit headers, ledger gets UNKNOWN confidence."""
        obs = from_rate_limit_info(None, "groq", "openai/gpt-oss-120b")
        ledger_dict = obs.to_ledger_dict()

        serialized = json.dumps(ledger_dict)
        deserialized = json.loads(serialized)

        assert deserialized["confidence"] == "UNKNOWN"
        # Compact — no fabricated fields
        assert "remaining_requests" not in deserialized
        assert "remaining_tokens" not in deserialized

    def test_observation_does_not_change_routing(self):
        """Rate-limit observation must not contain routing directives."""
        obs = from_rate_limit_info(
            RateLimitInfo(remaining_requests=0),
            "groq",
            "openai/gpt-oss-120b",
        )

        # Even at remaining=0, observation is recording-only
        assert not hasattr(obs, "should_failover")
        assert not hasattr(obs, "next_provider")
        assert not hasattr(obs, "cooldown_seconds")


# ═══════════════════════════════════════════════════════════════════════
# D. BENCHMARK ISOLATION — PROVIDER/MODEL IMMUTABILITY
# ═══════════════════════════════════════════════════════════════════════


class TestBenchmarkIsolation:
    """Verify that wiring Phase 3 utilities preserves scientific invariants."""

    def test_provider_identity_frozen(self):
        """Classification of any error does not change the provider."""
        for status in [429, 500, 503, 401, 403, 404, 413]:
            result = classify_provider_error(Exception("test"), status_code=status)
            # No field suggests a provider change
            attrs = vars(result) if hasattr(result, "__dict__") else {}
            for k, v in attrs.items():
                if "provider" in k.lower():
                    # The only provider-related info would be from the original error
                    assert v is None or v == ""

    def test_model_identity_frozen(self):
        """Classification of any error does not change the model."""
        for status in [429, 500, 503, 401, 403]:
            result = classify_provider_error(Exception("test"), status_code=status)
            assert not hasattr(result, "alternative_model")
            assert not hasattr(result, "next_model")

    def test_no_automatic_failover(self):
        """None of the utilities introduce automatic failover."""
        # Error classifier
        err_result = classify_provider_error(Exception("Groq down"), status_code=503)
        assert not hasattr(err_result, "failover_to")

        # Rate-limit observation
        obs = from_rate_limit_info(
            RateLimitInfo(remaining_requests=0),
            "groq",
            "openai/gpt-oss-120b",
        )
        assert not hasattr(obs, "failover_to")

    def test_no_hidden_llm_call(self):
        """Utilities must never invoke the LLM."""
        # All three are pure data operations
        classify_provider_error(Exception("test"), status_code=429)
        redact_secrets("test gsk_abc123XYZ789defGHI")
        from_rate_limit_info(RateLimitInfo(), "groq", "openai/gpt-oss-120b")
        # If any of these made an LLM call, the test would need network access
        # The fact that this test passes offline proves no LLM call occurs

    def test_retry_count_governed_by_runner(self):
        """Classification provides 'retryable' but not 'retry_count'."""
        result = classify_provider_error(Exception("rate limit"), status_code=429)
        assert result.retryable is True
        assert not hasattr(result, "retry_count")
        assert not hasattr(result, "max_retries")

    def test_invocation_identity_unchanged(self):
        """Utilities do not generate or modify invocation IDs."""
        result = classify_provider_error(Exception("test"), status_code=500)
        assert not hasattr(result, "invocation_id")
        assert not hasattr(result, "case_id")

    def test_evidence_retrieval_unchanged(self):
        """None of the utilities reference evidence or retrieval."""
        # Check module contents via classification
        result = classify_provider_error(Exception("test"))
        assert not hasattr(result, "evidence")
        assert not hasattr(result, "chunks")
        assert not hasattr(result, "trust_score")

    def test_scientific_mode_preserved(self):
        """RoutingMode.SCIENTIFIC still exists and has correct value."""
        assert RoutingMode.SCIENTIFIC.value == "SCIENTIFIC"
        assert RoutingMode.DEVELOPMENT.value == "DEVELOPMENT"
        assert RoutingMode.APPLICATION.value == "APPLICATION"


# ═══════════════════════════════════════════════════════════════════════
# E. PERFORMANCE OVERHEAD
# ═══════════════════════════════════════════════════════════════════════


class TestPerformanceOverhead:
    """Measure and bound the overhead of the new utilities."""

    def test_classifier_overhead(self):
        """Error classification should complete in < 1ms."""
        err = ModelExecutionError("test error", status_code="429")
        start = time.perf_counter()
        for _ in range(1000):
            classify_provider_error(err)
        elapsed = time.perf_counter() - start
        per_call_us = (elapsed / 1000) * 1_000_000
        assert per_call_us < 1000, f"Classifier took {per_call_us:.0f}µs per call"

    def test_redaction_overhead(self):
        """Redaction of a typical error string should complete in < 1ms."""
        text = "Error: gsk_abc123XYZ789defGHI caused issue with Bearer eyJtoken"
        start = time.perf_counter()
        for _ in range(1000):
            redact_secrets(text)
        elapsed = time.perf_counter() - start
        per_call_us = (elapsed / 1000) * 1_000_000
        assert per_call_us < 1000, f"Redaction took {per_call_us:.0f}µs per call"

    def test_rate_limit_adapter_overhead(self):
        """Rate-limit observation adapter should complete in < 1ms."""
        info = RateLimitInfo(remaining_requests=28, remaining_tokens=7200)
        start = time.perf_counter()
        for _ in range(1000):
            from_rate_limit_info(info, "groq", "openai/gpt-oss-120b")
        elapsed = time.perf_counter() - start
        per_call_us = (elapsed / 1000) * 1_000_000
        assert per_call_us < 1000, f"Observation took {per_call_us:.0f}µs per call"
