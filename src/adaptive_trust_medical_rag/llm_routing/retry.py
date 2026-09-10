from __future__ import annotations
import random
import time
from dataclasses import dataclass
from adaptive_trust_medical_rag.llm_routing.types import FailureClass, FAILOVER_ELIGIBLE


@dataclass
class RetryPolicy:
    """Bounded exponential backoff retry policy with jitter."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    jitter: bool = True

    def should_retry(self, failure_class: FailureClass, attempt: int) -> bool:
        """Return True if this failure class is retryable and attempts remain."""
        if attempt >= self.max_attempts:
            return False
        return failure_class in FAILOVER_ELIGIBLE

    def get_delay(self, attempt: int, retry_after: float | None = None) -> float:
        """Calculate delay for the given attempt number.
        
        Respects Retry-After when provided by the provider.
        """
        if retry_after is not None and retry_after > 0:
            return min(retry_after, self.max_delay)
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        if self.jitter:
            delay = delay * (0.5 + random.random() * 0.5)  # noqa: S311
        return delay

    @staticmethod
    def classify_failure(
        status_code: int | str | None = None,
        exception: Exception | None = None,
    ) -> FailureClass:
        """Map HTTP status codes and exceptions to the failure taxonomy."""
        if exception is not None:
            exc_type = type(exception).__name__.lower()
            exc_msg = str(exception).lower()
            if "timeout" in exc_type or "timeout" in exc_msg:
                return FailureClass.TIMEOUT
            if any(x in exc_type for x in ("connection", "network", "dns", "socket")):
                return FailureClass.NETWORK
            if any(x in exc_msg for x in ("connection", "network", "dns", "socket")):
                return FailureClass.NETWORK

        if status_code is not None:
            code = int(status_code) if isinstance(status_code, str) and status_code.isdigit() else status_code
            if isinstance(code, int):
                if code == 429:
                    return FailureClass.RATE_LIMIT
                if code == 401:
                    return FailureClass.AUTHENTICATION
                if code == 403:
                    return FailureClass.AUTHORIZATION
                if code == 400:
                    return FailureClass.INVALID_REQUEST
                if code == 404:
                    return FailureClass.MODEL_NOT_FOUND
                if code in (502, 503):
                    return FailureClass.TRANSIENT_PROVIDER
                if code == 504:
                    return FailureClass.TIMEOUT
                if code == 529:  # Some providers use this for capacity
                    return FailureClass.CAPACITY
            # String status codes from ModelExecutionError
            if isinstance(status_code, str):
                s = status_code.upper()
                if s == "TIMEOUT":
                    return FailureClass.TIMEOUT
                if s == "EMPTY_RESPONSE":
                    return FailureClass.TRANSIENT_PROVIDER
                if s in ("RATE_LIMITED", "RATE_LIMIT"):
                    return FailureClass.RATE_LIMIT

        return FailureClass.UNKNOWN
