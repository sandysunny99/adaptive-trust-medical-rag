"""Tests for FreeLLMAPI-adapted provider infrastructure utilities.

Covers:
    A. Error classification (provider_errors.py)
    B. Secret redaction (provider_redaction.py)
    C. Rate-limit telemetry observation (provider_rate_limit.py)
    D. Benchmark invariants (scientific isolation verification)
    E. Redaction false-positive controls (medical/RAG content safety)
"""

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
    RedactionResult,
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
# A. ERROR CLASSIFICATION TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestErrorClassificationByStatus:
    """HTTP status-first classification (most reliable signal)."""

    def test_429_rate_limit(self):
        err = Exception("Too many requests")
        result = classify_provider_error(err, status_code=429)
        assert result.failure_class == FailureClass.RATE_LIMIT
        assert result.retryable is True
        assert result.http_status == 429

    def test_500_server_error(self):
        err = Exception("Internal server error")
        result = classify_provider_error(err, status_code=500)
        assert result.failure_class == FailureClass.TRANSIENT_PROVIDER
        assert result.retryable is True
        assert result.http_status == 500

    def test_502_bad_gateway(self):
        err = Exception("Bad gateway")
        result = classify_provider_error(err, status_code=502)
        assert result.failure_class == FailureClass.TRANSIENT_PROVIDER
        assert result.retryable is True

    def test_503_service_unavailable(self):
        err = Exception("Service unavailable")
        result = classify_provider_error(err, status_code=503)
        assert result.failure_class == FailureClass.TRANSIENT_PROVIDER
        assert result.retryable is True

    def test_504_gateway_timeout(self):
        err = Exception("Gateway timeout")
        result = classify_provider_error(err, status_code=504)
        assert result.failure_class == FailureClass.TRANSIENT_PROVIDER
        assert result.retryable is True

    def test_401_authentication(self):
        err = Exception("Unauthorized")
        result = classify_provider_error(err, status_code=401)
        assert result.failure_class == FailureClass.AUTHENTICATION
        assert result.retryable is False

    def test_403_authorization(self):
        err = Exception("Forbidden")
        result = classify_provider_error(err, status_code=403)
        assert result.failure_class == FailureClass.AUTHORIZATION
        assert result.retryable is False

    def test_404_model_not_found(self):
        err = Exception("Not found")
        result = classify_provider_error(err, status_code=404)
        assert result.failure_class == FailureClass.MODEL_NOT_FOUND
        assert result.retryable is False

    def test_400_invalid_request(self):
        err = Exception("Bad request")
        result = classify_provider_error(err, status_code=400)
        # 400 not in explicit map → falls through to message/unknown
        # unless message matches
        assert result.failure_class in (FailureClass.UNKNOWN, FailureClass.INVALID_REQUEST)

    def test_413_context_too_large(self):
        err = Exception("Payload too large")
        result = classify_provider_error(err, status_code=413)
        assert result.failure_class == FailureClass.INVALID_REQUEST
        assert result.detail == "CONTEXT_TOO_LARGE"
        assert result.retryable is True

    def test_402_payment_required(self):
        err = Exception("Payment required")
        result = classify_provider_error(err, status_code=402)
        assert result.failure_class == FailureClass.AUTHORIZATION
        assert result.detail == "PAYMENT_REQUIRED"
        assert result.retryable is False

    def test_422_validation(self):
        err = Exception("Unprocessable entity")
        result = classify_provider_error(err, status_code=422)
        assert result.failure_class == FailureClass.INVALID_REQUEST
        assert result.retryable is False

    def test_unknown_5xx(self):
        """5xx not in explicit map → TRANSIENT_PROVIDER."""
        err = Exception("Unknown server error")
        result = classify_provider_error(err, status_code=507)
        assert result.failure_class == FailureClass.TRANSIENT_PROVIDER
        assert result.retryable is True
        assert result.http_status == 507


class TestErrorClassificationByException:
    """Exception-type classification when no HTTP status available."""

    def test_model_execution_error_with_status(self):
        err = ModelExecutionError("Groq error", status_code="429")
        result = classify_provider_error(err)
        assert result.failure_class == FailureClass.RATE_LIMIT
        assert result.http_status == 429

    def test_model_execution_error_timeout(self):
        err = ModelExecutionError("Timed out", status_code="TIMEOUT")
        result = classify_provider_error(err)
        # status_code="TIMEOUT" is not an int → falls to message
        assert result.failure_class == FailureClass.TIMEOUT

    def test_model_execution_error_empty(self):
        err = ModelExecutionError("Empty response from Groq API", status_code="EMPTY_RESPONSE")
        result = classify_provider_error(err)
        assert result.failure_class == FailureClass.UNKNOWN
        assert result.detail == "MALFORMED_RESPONSE"

    def test_unknown_exception(self):
        err = ValueError("something unexpected")
        result = classify_provider_error(err)
        assert result.failure_class == FailureClass.UNKNOWN
        assert result.retryable is False


class TestErrorClassificationByMessage:
    """Message-substring fallback classification."""

    def test_rate_limit_in_message(self):
        err = Exception("Error: rate limit exceeded on Groq")
        result = classify_provider_error(err)
        assert result.failure_class == FailureClass.RATE_LIMIT
        assert result.retryable is True

    def test_429_in_message(self):
        err = Exception("Groq API error (status 429): Too many requests")
        result = classify_provider_error(err)
        assert result.failure_class == FailureClass.RATE_LIMIT

    def test_quota_in_message(self):
        err = Exception("Quota exhausted for this model")
        result = classify_provider_error(err)
        assert result.failure_class == FailureClass.RATE_LIMIT

    def test_timeout_in_message(self):
        err = Exception("Request timeout after 30s")
        result = classify_provider_error(err)
        assert result.failure_class == FailureClass.TIMEOUT

    def test_unavailable_in_message(self):
        err = Exception("Service unavailable, try again")
        result = classify_provider_error(err)
        assert result.failure_class == FailureClass.TRANSIENT_PROVIDER


class TestErrorClassificationRetryEligibility:
    """Verify retryable classifications align with FAILOVER_ELIGIBLE."""

    def test_rate_limit_in_failover_eligible(self):
        assert FailureClass.RATE_LIMIT in FAILOVER_ELIGIBLE

    def test_transient_in_failover_eligible(self):
        assert FailureClass.TRANSIENT_PROVIDER in FAILOVER_ELIGIBLE

    def test_timeout_in_failover_eligible(self):
        assert FailureClass.TIMEOUT in FAILOVER_ELIGIBLE

    def test_network_in_failover_eligible(self):
        assert FailureClass.NETWORK in FAILOVER_ELIGIBLE

    def test_auth_not_in_failover_eligible(self):
        assert FailureClass.AUTHENTICATION not in FAILOVER_ELIGIBLE

    def test_authorization_not_in_failover_eligible(self):
        assert FailureClass.AUTHORIZATION not in FAILOVER_ELIGIBLE

    def test_model_not_found_not_eligible(self):
        assert FailureClass.MODEL_NOT_FOUND not in FAILOVER_ELIGIBLE

    def test_unknown_not_eligible(self):
        assert FailureClass.UNKNOWN not in FAILOVER_ELIGIBLE


class TestErrorClassificationContract:
    """Verify the classification contract."""

    def test_result_is_dataclass(self):
        result = classify_provider_error(Exception("test"))
        assert isinstance(result, ProviderErrorClassification)

    def test_result_has_required_fields(self):
        result = classify_provider_error(Exception("test"))
        assert hasattr(result, "failure_class")
        assert hasattr(result, "retryable")
        assert hasattr(result, "reason_code")
        assert hasattr(result, "http_status")
        assert hasattr(result, "detail")

    def test_explicit_status_overrides_message(self):
        """Status code wins over message content."""
        err = Exception("rate limit exceeded")
        result = classify_provider_error(err, status_code=401)
        assert result.failure_class == FailureClass.AUTHENTICATION

    def test_classification_is_deterministic(self):
        """Same input → same output."""
        err = Exception("Groq API error (status 429)")
        r1 = classify_provider_error(err, status_code=429)
        r2 = classify_provider_error(err, status_code=429)
        assert r1.failure_class == r2.failure_class
        assert r1.retryable == r2.retryable
        assert r1.reason_code == r2.reason_code


# ═══════════════════════════════════════════════════════════════════════
# B. SECRET REDACTION TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestRedactionProviderKeys:
    """Verify known provider key formats are redacted."""

    def test_groq_key(self):
        text = "Error with key gsk_abc123XYZ789defGHI"
        assert "[REDACTED]" in redact_secrets(text)
        assert "gsk_abc123" not in redact_secrets(text)

    def test_openai_key(self):
        text = "Using sk-abc123XYZ789defGHI012345"
        assert "[REDACTED]" in redact_secrets(text)
        assert "sk-abc123" not in redact_secrets(text)

    def test_google_key(self):
        text = "Key AIzaSyCabcdefghijklmnopqrstuvwx"
        assert "[REDACTED]" in redact_secrets(text)
        assert "AIzaSyC" not in redact_secrets(text)

    def test_nvidia_key(self):
        text = "Set nvapi-abc123XYZ789def"
        assert "[REDACTED]" in redact_secrets(text)
        assert "nvapi-" not in redact_secrets(text)

    def test_huggingface_token(self):
        text = "Token hf_abcdefghijklmnop1234"
        assert "[REDACTED]" in redact_secrets(text)
        assert "hf_abcdefg" not in redact_secrets(text)

    def test_cerebras_key(self):
        text = "Using csk-abcdefghijklmn"
        assert "[REDACTED]" in redact_secrets(text)
        assert "csk-abcd" not in redact_secrets(text)


class TestRedactionBearerTokens:
    """Verify bearer token and auth header redaction."""

    def test_bearer_token(self):
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig"
        result = redact_secrets(text)
        # The credential value must be removed regardless of exact format
        assert "eyJhbG" not in result
        assert "payload.sig" not in result
        assert "[REDACTED]" in result

    def test_bearer_case_insensitive(self):
        text = "bearer gsk_abc123XYZ789defGHI"
        result = redact_secrets(text)
        assert "gsk_abc" not in result

    def test_authorization_header_json(self):
        text = '{"authorization": "sk-abc123XYZ789defGHI"}'
        result = redact_secrets(text)
        assert "sk-abc123" not in result


class TestRedactionMultipleSecrets:
    """Multiple secrets in one string."""

    def test_two_different_keys(self):
        text = "Key1: gsk_abc123XYZ789defGHI, Key2: sk-xyz987ABC654"
        result = redact_secrets(text)
        assert "gsk_abc" not in result
        assert "sk-xyz" not in result
        assert result.count("[REDACTED]") >= 2

    def test_detailed_count(self):
        text = "gsk_abc123XYZ789defGHI and sk-xyz987ABC654mno"
        result = redact_secrets_detailed(text)
        assert isinstance(result, RedactionResult)
        assert result.redaction_count >= 2
        assert "gsk_abc" not in result.text


class TestRedactionFalsePositiveControls:
    """CRITICAL: Verify that legitimate content is NOT redacted."""

    def test_case_id_preserved(self):
        text = "case_id=CASE_001_BENIGN"
        assert redact_secrets(text) == text

    def test_run_id_preserved(self):
        text = "run_id=FREE_REP_V2_RUN1"
        assert redact_secrets(text) == text

    def test_document_id_preserved(self):
        text = "document_id=fda_label_warfarin_2024"
        assert redact_secrets(text) == text

    def test_source_url_preserved(self):
        text = "source_url=https://pubmed.ncbi.nlm.nih.gov/12345678"
        assert redact_secrets(text) == text

    def test_sha256_hash_preserved(self):
        text = "content_hash=af71c70d36081b1b68316b5ff8636969c8b964c9655f752b41112694ebc02c48"
        assert redact_secrets(text) == text

    def test_publication_date_preserved(self):
        text = "publication_date=2024-01-15"
        assert redact_secrets(text) == text

    def test_trust_score_preserved(self):
        text = "trust_score=0.57"
        assert redact_secrets(text) == text

    def test_clinical_terminology_preserved(self):
        text = "Warfarin sodium 5mg tablets, INR monitoring required"
        assert redact_secrets(text) == text

    def test_drug_names_preserved(self):
        text = "Metformin HCl 500mg, Lisinopril 10mg, Atorvastatin 20mg"
        assert redact_secrets(text) == text

    def test_evidence_text_preserved(self):
        text = (
            "Evidence: Co-administration of warfarin and aspirin increases "
            "bleeding risk. Source authority: FDA, tier 1."
        )
        assert redact_secrets(text) == text

    def test_normal_error_message_preserved(self):
        text = "Groq API error (status 503): Service temporarily unavailable"
        assert redact_secrets(text) == text

    def test_bearer_word_in_normal_text_not_redacted(self):
        """The word 'Bearer' alone without a token should not be redacted."""
        text = "The Bearer of this document"
        # 'Bearer' followed by non-token-like chars
        result = redact_secrets(text)
        # "of" doesn't match [A-Za-z0-9._~+/\-]+=* in sufficient length
        assert "document" in result

    def test_short_sk_prefix_not_redacted(self):
        """'sk-' with fewer than 8 chars should not match."""
        text = "sk-short"
        assert redact_secrets(text) == text

    def test_source_id_preserved(self):
        text = "source_id=pubmed_38291045"
        assert redact_secrets(text) == text

    def test_nested_json_preserved(self):
        text = '{"case_id": "C001", "status": "released", "trust": 0.58}'
        assert redact_secrets(text) == text

    def test_content_hash_field_preserved(self):
        text = "content_hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert redact_secrets(text) == text


# ═══════════════════════════════════════════════════════════════════════
# C. RATE-LIMIT TELEMETRY TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestRateLimitObservation:
    """Test the from_rate_limit_info() adapter."""

    def test_all_headers_present(self):
        info = RateLimitInfo(
            limit_requests=30,
            remaining_requests=28,
            reset_requests="2m59.123s",
            limit_tokens=8000,
            remaining_tokens=7200,
            reset_tokens="1m30s",
            retry_after=None,
        )
        obs = from_rate_limit_info(info, "groq", "openai/gpt-oss-120b")
        assert obs.confidence == TelemetryConfidence.OBSERVED
        assert obs.remaining_requests == 28
        assert obs.request_limit == 30
        assert obs.remaining_tokens == 7200
        assert obs.token_limit == 8000
        assert obs.request_reset == "2m59.123s"
        assert obs.provider == "groq"
        assert obs.model == "openai/gpt-oss-120b"

    def test_partial_headers_retry_after_only(self):
        info = RateLimitInfo(retry_after=35.0)
        obs = from_rate_limit_info(info, "groq", "openai/gpt-oss-120b")
        assert obs.confidence == TelemetryConfidence.OBSERVED
        assert obs.retry_after_seconds == 35.0
        assert obs.remaining_requests is None
        assert obs.remaining_tokens is None

    def test_partial_headers_reset_only(self):
        info = RateLimitInfo(reset_requests="1m30s")
        obs = from_rate_limit_info(info, "groq", "openai/gpt-oss-120b")
        assert obs.confidence == TelemetryConfidence.OBSERVED
        assert obs.request_reset == "1m30s"

    def test_missing_headers_none_info(self):
        obs = from_rate_limit_info(None, "groq", "openai/gpt-oss-120b")
        assert obs.confidence == TelemetryConfidence.UNKNOWN
        assert obs.remaining_requests is None
        assert obs.remaining_tokens is None
        assert obs.retry_after_seconds is None

    def test_empty_info_all_none(self):
        info = RateLimitInfo()  # All fields default to None
        obs = from_rate_limit_info(info, "groq", "openai/gpt-oss-120b")
        assert obs.confidence == TelemetryConfidence.UNKNOWN

    def test_never_fabricate_missing(self):
        """Missing headers → None, never 0 or default values."""
        info = RateLimitInfo(remaining_requests=28)
        obs = from_rate_limit_info(info, "groq", "openai/gpt-oss-120b")
        assert obs.remaining_tokens is None  # Not 0
        assert obs.token_limit is None  # Not 0
        assert obs.retry_after_seconds is None  # Not 0

    def test_observed_at_is_iso_timestamp(self):
        obs = from_rate_limit_info(None, "groq", "openai/gpt-oss-120b")
        # Should be parseable ISO 8601
        assert "T" in obs.observed_at
        assert ":" in obs.observed_at


class TestRateLimitLedgerSerialization:
    """Test to_ledger_dict() for invocation ledger compatibility."""

    def test_full_observation_serialization(self):
        info = RateLimitInfo(
            limit_requests=30,
            remaining_requests=28,
            limit_tokens=8000,
            remaining_tokens=7200,
            retry_after=None,
        )
        obs = from_rate_limit_info(info, "groq", "openai/gpt-oss-120b")
        d = obs.to_ledger_dict()
        assert d["confidence"] == "OBSERVED"
        assert d["remaining_requests"] == 28
        assert d["request_limit"] == 30
        assert "observed_at" in d

    def test_empty_observation_serialization(self):
        obs = from_rate_limit_info(None, "groq", "openai/gpt-oss-120b")
        d = obs.to_ledger_dict()
        assert d["confidence"] == "UNKNOWN"
        assert "remaining_requests" not in d
        assert "remaining_tokens" not in d

    def test_partial_observation_compact(self):
        """Only non-None fields appear in ledger dict."""
        info = RateLimitInfo(remaining_requests=5)
        obs = from_rate_limit_info(info, "groq", "openai/gpt-oss-120b")
        d = obs.to_ledger_dict()
        assert "remaining_requests" in d
        assert "remaining_tokens" not in d
        assert "token_limit" not in d


# ═══════════════════════════════════════════════════════════════════════
# D. BENCHMARK INVARIANT TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestBenchmarkInvariants:
    """Verify that the new utilities do NOT alter scientific semantics."""

    def test_invariant_1_scientific_mode_exists(self):
        """RoutingMode.SCIENTIFIC remains defined."""
        assert RoutingMode.SCIENTIFIC.value == "SCIENTIFIC"

    def test_invariant_2_failure_class_unchanged(self):
        """Original 11 FailureClass members still exist."""
        expected = {
            "TRANSIENT_PROVIDER", "RATE_LIMIT", "TIMEOUT", "CAPACITY",
            "NETWORK", "AUTHENTICATION", "AUTHORIZATION", "INVALID_REQUEST",
            "MODEL_NOT_FOUND", "SCHEMA_ERROR", "APPLICATION_SEMANTIC", "UNKNOWN",
        }
        actual = {m.value for m in FailureClass}
        assert expected.issubset(actual), f"Missing: {expected - actual}"

    def test_invariant_3_failover_eligible_unchanged(self):
        """FAILOVER_ELIGIBLE frozenset is unchanged."""
        expected = frozenset({
            FailureClass.TRANSIENT_PROVIDER,
            FailureClass.RATE_LIMIT,
            FailureClass.TIMEOUT,
            FailureClass.CAPACITY,
            FailureClass.NETWORK,
        })
        assert FAILOVER_ELIGIBLE == expected

    def test_invariant_4_classifier_no_side_effects(self):
        """classify_provider_error is pure — no state mutation."""
        err = Exception("test")
        r1 = classify_provider_error(err, status_code=429)
        r2 = classify_provider_error(err, status_code=429)
        assert r1.failure_class == r2.failure_class
        assert r1.retryable == r2.retryable

    def test_invariant_5_redaction_no_scientific_mutation(self):
        """Redaction does not alter scientific observation content."""
        scientific_text = (
            "case_id=C001 status=released trust=0.58 "
            "gate=release confidence=0.60"
        )
        assert redact_secrets(scientific_text) == scientific_text

    def test_invariant_6_rate_limit_observation_only(self):
        """RateLimitObservation is frozen (immutable)."""
        obs = from_rate_limit_info(None, "groq", "openai/gpt-oss-120b")
        with pytest.raises(AttributeError):
            obs.remaining_requests = 42  # type: ignore[misc]

    def test_invariant_7_no_provider_change(self):
        """Error classification does not contain provider-switching logic."""
        err = Exception("Groq API error (status 429)")
        result = classify_provider_error(err, status_code=429)
        # Classification is metadata only — no 'next_provider' field
        assert not hasattr(result, "next_provider")
        assert not hasattr(result, "fallback_model")

    def test_invariant_8_no_hidden_retry_count(self):
        """Classification does not include retry directives."""
        result = classify_provider_error(Exception("test"), status_code=500)
        assert not hasattr(result, "retry_count")
        assert not hasattr(result, "max_retries")

    def test_invariant_9_classification_does_not_change_existing_failover(self):
        """New detail values do not affect FAILOVER_ELIGIBLE membership."""
        err = Exception("Payload too large")
        result = classify_provider_error(err, status_code=413)
        # INVALID_REQUEST is NOT in FAILOVER_ELIGIBLE
        assert result.failure_class not in FAILOVER_ELIGIBLE

    def test_invariant_10_rate_limit_info_dataclass_unchanged(self):
        """RateLimitInfo still has exactly 7 fields."""
        info = RateLimitInfo()
        fields = [f.name for f in info.__dataclass_fields__.values()]
        assert set(fields) == {
            "limit_requests", "remaining_requests", "reset_requests",
            "limit_tokens", "remaining_tokens", "reset_tokens",
            "retry_after",
        }
