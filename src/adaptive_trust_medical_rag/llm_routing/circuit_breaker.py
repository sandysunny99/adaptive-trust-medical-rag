from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from adaptive_trust_medical_rag.llm_routing.types import (
    FAILOVER_ELIGIBLE,
    CircuitState,
    FailureClass,
)


@dataclass
class CircuitBreaker:
    """Per-provider circuit breaker.
    
    Only transient/availability failures count toward opening.
    Security decisions (BLOCK, authorization denial, claim failure)
    do NOT affect circuit state.
    """
    provider_name: str
    failure_threshold: int = 5
    recovery_timeout_seconds: float = 60.0
    half_open_max_calls: int = 1

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _half_open_calls: int = field(default=0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                if time.monotonic() - self._last_failure_time >= self.recovery_timeout_seconds:
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
            return self._state

    def allow_request(self) -> bool:
        """Check if a request should be allowed through."""
        current = self.state
        if current == CircuitState.CLOSED:
            return True
        if current == CircuitState.HALF_OPEN:
            with self._lock:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
            return False
        return False  # OPEN

    def record_success(self) -> None:
        """Record a successful call. Resets circuit to CLOSED."""
        with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED
            self._half_open_calls = 0

    def record_failure(self, failure_class: FailureClass) -> None:
        """Record a failure. Only availability failures count."""
        if failure_class not in FAILOVER_ELIGIBLE:
            return  # Don't count non-transient failures
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._half_open_calls = 0
