"""Rate-limit telemetry observation for provider responses.

Records provider rate-limit header information as structured telemetry
for the invocation ledger. This is OBSERVATION ONLY — it does not
change backoff timing, retry policy, provider selection, or model choice.

Adapted from provider-quota header-observation patterns in FreeLLMAPI
(MIT, tashfeenahmed/freellmapi), translated to Python.

This module does NOT:
- select providers
- switch models
- perform failover
- alter scientific benchmark conditions
- change trust scores or evidence eligibility

Integration point:
    GroqBackend.last_rate_limit_info (existing RateLimitInfo)
        → to_observation() adapter
        → serialized as rate_limit_snapshot in invocation ledger
"""

from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from adaptive_trust_medical_rag.llm_routing.types import RateLimitInfo


class TelemetryConfidence(str, enum.Enum):
    """Confidence level for rate-limit observations.

    OBSERVED: Values directly from provider response headers.
    UNKNOWN:  No provider data available — fields are None.

    We intentionally do NOT have an ESTIMATED level. Missing data
    is represented as None, never as fabricated default values.
    """

    OBSERVED = "OBSERVED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RateLimitObservation:
    """Normalized rate-limit telemetry from a single provider response.

    All numeric fields are None when not provided by the provider.
    We never fabricate values for missing headers.
    """

    provider: str
    model: str
    observed_at: str  # ISO 8601 timestamp

    # Request windows
    request_limit: int | None = None
    remaining_requests: int | None = None
    request_reset: str | None = None  # Duration string or timestamp

    # Token windows
    token_limit: int | None = None
    remaining_tokens: int | None = None
    token_reset: str | None = None

    # Retry guidance
    retry_after_seconds: float | None = None

    # Metadata
    confidence: TelemetryConfidence = TelemetryConfidence.UNKNOWN

    def to_ledger_dict(self) -> dict[str, Any]:
        """Serialize to a flat dict suitable for the invocation ledger.

        Only includes fields with non-None values to keep ledger entries
        compact and backward-compatible with older records.
        """
        result: dict[str, Any] = {
            "confidence": self.confidence.value,
            "observed_at": self.observed_at,
        }
        if self.remaining_requests is not None:
            result["remaining_requests"] = self.remaining_requests
        if self.request_limit is not None:
            result["request_limit"] = self.request_limit
        if self.remaining_tokens is not None:
            result["remaining_tokens"] = self.remaining_tokens
        if self.token_limit is not None:
            result["token_limit"] = self.token_limit
        if self.retry_after_seconds is not None:
            result["retry_after_seconds"] = self.retry_after_seconds
        if self.request_reset is not None:
            result["request_reset"] = self.request_reset
        if self.token_reset is not None:
            result["token_reset"] = self.token_reset
        return result


def from_rate_limit_info(
    info: RateLimitInfo | None,
    provider: str,
    model: str,
) -> RateLimitObservation:
    """Adapt the existing RateLimitInfo into a RateLimitObservation.

    This is the primary integration point: GroqBackend already parses
    rate-limit headers into RateLimitInfo. This function wraps that
    existing data into the observation format for ledger recording.

    Args:
        info: Existing RateLimitInfo from the backend, or None.
        provider: Provider name (e.g. 'groq').
        model: Model identifier (e.g. 'openai/gpt-oss-120b').

    Returns:
        RateLimitObservation with OBSERVED confidence if info is
        non-None and has at least one populated field, UNKNOWN otherwise.
    """
    now = datetime.now(timezone.utc).isoformat()

    if info is None:
        return RateLimitObservation(
            provider=provider,
            model=model,
            observed_at=now,
            confidence=TelemetryConfidence.UNKNOWN,
        )

    # Determine confidence: OBSERVED if any field has data
    has_data = any([
        info.remaining_requests is not None,
        info.remaining_tokens is not None,
        info.limit_requests is not None,
        info.limit_tokens is not None,
        info.retry_after is not None,
        info.reset_requests is not None,
        info.reset_tokens is not None,
    ])

    return RateLimitObservation(
        provider=provider,
        model=model,
        observed_at=now,
        request_limit=info.limit_requests,
        remaining_requests=info.remaining_requests,
        request_reset=info.reset_requests,
        token_limit=info.limit_tokens,
        remaining_tokens=info.remaining_tokens,
        token_reset=info.reset_tokens,
        retry_after_seconds=info.retry_after,
        confidence=TelemetryConfidence.OBSERVED if has_data else TelemetryConfidence.UNKNOWN,
    )
