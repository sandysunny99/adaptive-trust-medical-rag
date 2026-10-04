"""Structured provider-error classifier for LLM backend failures.

Classifies upstream provider errors into the project's existing
FailureClass taxonomy. Adapted from error-classification patterns in
FreeLLMAPI (MIT, tashfeenahmed/freellmapi), translated to idiomatic
Python for our provider adapter layer.

This module is ENGINEERING INFRASTRUCTURE only. It does NOT:
- alter retry policy or attempt count
- change provider/model selection
- affect trust scoring or evidence eligibility
- modify security gate behaviour

Integration point:
    Provider error → classify_provider_error() → FailureClass
    → recorded in invocation ledger as structured metadata
    → existing retry controller uses its own policy unchanged
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_routing.types import FailureClass


# ── Additional failure classes for adapter-layer use only ─────────────
# These extend the base taxonomy without modifying the shared enum.
# They map to the closest FailureClass member when serialized to the
# invocation ledger, preserving backward compatibility with V1/V2
# artifacts.

ADAPTER_FAILURE_DETAIL: dict[str, FailureClass] = {
    "CONTEXT_TOO_LARGE": FailureClass.INVALID_REQUEST,
    "PAYMENT_REQUIRED": FailureClass.AUTHORIZATION,
    "MALFORMED_RESPONSE": FailureClass.UNKNOWN,
}


@dataclass(frozen=True)
class ProviderErrorClassification:
    """Structured classification of a provider error.

    Attributes:
        failure_class: The canonical FailureClass from the project taxonomy.
        detail: Optional finer-grained classification string (e.g.
            'CONTEXT_TOO_LARGE') when the base enum is too coarse.
        retryable: Whether the existing retry policy should consider this
            error eligible for retry. This is a *characterisation*, not a
            directive — the retry controller makes its own decision.
        http_status: The upstream HTTP status code, if available.
        reason_code: Human-readable reason string for ledger recording.
    """

    failure_class: FailureClass
    detail: str | None = None
    retryable: bool = False
    http_status: int | None = None
    reason_code: str = "UNKNOWN"


# ── HTTP status → classification mapping ──────────────────────────────
# Ordered by specificity. Status code is the most reliable signal
# (matches FreeLLMAPI's "trust the structured status first" principle).

_STATUS_MAP: dict[int, tuple[FailureClass, str | None, bool, str]] = {
    # (status) → (failure_class, detail, retryable, reason_code)
    401: (FailureClass.AUTHENTICATION, None, False, "AUTH_INVALID_KEY"),
    402: (FailureClass.AUTHORIZATION, "PAYMENT_REQUIRED", False, "PAYMENT_REQUIRED"),
    403: (FailureClass.AUTHORIZATION, None, False, "AUTH_FORBIDDEN"),
    404: (FailureClass.MODEL_NOT_FOUND, None, False, "MODEL_NOT_FOUND"),
    408: (FailureClass.TIMEOUT, None, True, "REQUEST_TIMEOUT"),
    410: (FailureClass.MODEL_NOT_FOUND, None, False, "MODEL_REMOVED"),
    413: (FailureClass.INVALID_REQUEST, "CONTEXT_TOO_LARGE", True, "CONTEXT_TOO_LARGE"),
    422: (FailureClass.INVALID_REQUEST, None, False, "VALIDATION_ERROR"),
    429: (FailureClass.RATE_LIMIT, None, True, "RATE_LIMITED"),
    500: (FailureClass.TRANSIENT_PROVIDER, None, True, "INTERNAL_SERVER_ERROR"),
    502: (FailureClass.TRANSIENT_PROVIDER, None, True, "BAD_GATEWAY"),
    503: (FailureClass.TRANSIENT_PROVIDER, None, True, "SERVICE_UNAVAILABLE"),
    504: (FailureClass.TRANSIENT_PROVIDER, None, True, "GATEWAY_TIMEOUT"),
}

# ── Message substring fallbacks ───────────────────────────────────────
# Used only when no HTTP status is available. Minimal set — not the 20+
# patterns from FreeLLMAPI, since we use a single provider (Groq).

_MESSAGE_PATTERNS: list[tuple[str, FailureClass, str | None, bool, str]] = [
    # (substring, failure_class, detail, retryable, reason_code)
    ("429", FailureClass.RATE_LIMIT, None, True, "RATE_LIMIT_IN_MESSAGE"),
    ("rate limit", FailureClass.RATE_LIMIT, None, True, "RATE_LIMIT_IN_MESSAGE"),
    ("too many requests", FailureClass.RATE_LIMIT, None, True, "RATE_LIMIT_IN_MESSAGE"),
    ("quota", FailureClass.RATE_LIMIT, None, True, "QUOTA_IN_MESSAGE"),
    ("resource_exhausted", FailureClass.RATE_LIMIT, None, True, "RESOURCE_EXHAUSTED"),
    ("timeout", FailureClass.TIMEOUT, None, True, "TIMEOUT_IN_MESSAGE"),
    ("timed out", FailureClass.TIMEOUT, None, True, "TIMEOUT_IN_MESSAGE"),
    ("empty response", FailureClass.UNKNOWN, "MALFORMED_RESPONSE", True, "EMPTY_RESPONSE"),
    ("empty content", FailureClass.UNKNOWN, "MALFORMED_RESPONSE", True, "EMPTY_CONTENT"),
    ("unavailable", FailureClass.TRANSIENT_PROVIDER, None, True, "UNAVAILABLE_IN_MESSAGE"),
    ("internal server error", FailureClass.TRANSIENT_PROVIDER, None, True, "ISE_IN_MESSAGE"),
]


def classify_provider_error(
    error: Exception,
    status_code: int | None = None,
) -> ProviderErrorClassification:
    """Classify a provider error into the project's FailureClass taxonomy.

    Classification priority (most reliable first):
        1. Explicit HTTP status code parameter
        2. status_code attribute on ModelExecutionError
        3. HTTP status from httpx response exceptions
        4. Exception type (TimeoutException, ConnectError, etc.)
        5. Error message substring matching (fallback)
        6. UNKNOWN

    This function is deterministic and side-effect-free. It does NOT
    change retry policy, provider selection, or scientific observations.

    Args:
        error: The exception raised by the provider call.
        status_code: Optional explicit HTTP status code. Takes priority
            over any status inferred from the exception.

    Returns:
        ProviderErrorClassification with structured metadata.
    """
    # 1. Resolve HTTP status from all available sources
    resolved_status = _resolve_status(error, status_code)

    # 2. Status-first classification (most reliable signal)
    if resolved_status is not None and resolved_status in _STATUS_MAP:
        fc, detail, retryable, reason = _STATUS_MAP[resolved_status]
        return ProviderErrorClassification(
            failure_class=fc,
            detail=detail,
            retryable=retryable,
            http_status=resolved_status,
            reason_code=reason,
        )

    # 3. Status in 5xx range not in explicit map
    if resolved_status is not None and resolved_status >= 500:
        return ProviderErrorClassification(
            failure_class=FailureClass.TRANSIENT_PROVIDER,
            retryable=True,
            http_status=resolved_status,
            reason_code=f"SERVER_ERROR_{resolved_status}",
        )

    # 4. Exception-type classification (Python-native, not cause-chain)
    if isinstance(error, httpx.TimeoutException):
        return ProviderErrorClassification(
            failure_class=FailureClass.TIMEOUT,
            retryable=True,
            http_status=resolved_status,
            reason_code="HTTPX_TIMEOUT",
        )

    if isinstance(error, httpx.ConnectError):
        return ProviderErrorClassification(
            failure_class=FailureClass.NETWORK,
            retryable=True,
            http_status=resolved_status,
            reason_code="HTTPX_CONNECT_ERROR",
        )

    if isinstance(error, (httpx.NetworkError, ConnectionError, OSError)):
        return ProviderErrorClassification(
            failure_class=FailureClass.NETWORK,
            retryable=True,
            http_status=resolved_status,
            reason_code="NETWORK_ERROR",
        )

    # 5. Message substring fallback
    msg = str(error).lower()
    for pattern, fc, detail, retryable, reason in _MESSAGE_PATTERNS:
        if pattern in msg:
            return ProviderErrorClassification(
                failure_class=fc,
                detail=detail,
                retryable=retryable,
                http_status=resolved_status,
                reason_code=reason,
            )

    # 6. Unknown
    return ProviderErrorClassification(
        failure_class=FailureClass.UNKNOWN,
        retryable=False,
        http_status=resolved_status,
        reason_code="UNCLASSIFIED",
    )


def _resolve_status(error: Exception, explicit_status: int | None) -> int | None:
    """Extract HTTP status code from all available sources."""
    # Explicit parameter always wins
    if explicit_status is not None:
        return explicit_status

    # ModelExecutionError carries status_code as string
    if isinstance(error, ModelExecutionError):
        try:
            return int(error.status_code)
        except (ValueError, TypeError):
            pass

    # httpx HTTPStatusError carries response.status_code
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code

    # Generic 'status' attribute
    status = getattr(error, "status", None)
    if isinstance(status, int):
        return status

    return None
