from __future__ import annotations
import statistics
import threading
from datetime import UTC, datetime
from adaptive_trust_medical_rag.llm_routing.types import (
    CircuitState,
    FailureClass,
    ProviderHealth,
    RateLimitInfo,
)

_MAX_LATENCY_WINDOW = 100  # Keep last N latencies for percentile calculation


class ProviderHealthRegistry:
    """Tracks health state for all configured providers.
    
    Never stores API secrets.
    """

    def __init__(self) -> None:
        self._providers: dict[str, ProviderHealth] = {}
        self._lock = threading.Lock()

    def register(self, provider_name: str) -> None:
        with self._lock:
            if provider_name not in self._providers:
                self._providers[provider_name] = ProviderHealth(
                    provider_name=provider_name
                )

    def record_success(
        self,
        provider: str,
        latency_ms: float,
        rate_limit_info: RateLimitInfo | None = None,
    ) -> None:
        with self._lock:
            h = self._providers.get(provider)
            if h is None:
                return
            h.available = True
            h.consecutive_failures = 0
            h.total_successes += 1
            h.last_success = datetime.now(UTC).isoformat()
            h.latencies.append(latency_ms)
            if len(h.latencies) > _MAX_LATENCY_WINDOW:
                h.latencies = h.latencies[-_MAX_LATENCY_WINDOW:]
            if rate_limit_info:
                h.quota_remaining_requests = rate_limit_info.remaining_requests
                h.quota_remaining_tokens = rate_limit_info.remaining_tokens
            h.health_timestamp = datetime.now(UTC).isoformat()

    def record_failure(
        self,
        provider: str,
        failure_class: FailureClass,
        rate_limit_info: RateLimitInfo | None = None,
    ) -> None:
        with self._lock:
            h = self._providers.get(provider)
            if h is None:
                return
            h.consecutive_failures += 1
            h.total_failures += 1
            h.last_failure = datetime.now(UTC).isoformat()
            if failure_class == FailureClass.RATE_LIMIT:
                h.rate_limit_events += 1
            if rate_limit_info:
                h.quota_remaining_requests = rate_limit_info.remaining_requests
                h.quota_remaining_tokens = rate_limit_info.remaining_tokens
            h.health_timestamp = datetime.now(UTC).isoformat()

    def update_circuit_state(self, provider: str, state: CircuitState) -> None:
        with self._lock:
            h = self._providers.get(provider)
            if h:
                h.circuit_state = state

    def get_health(self, provider: str) -> ProviderHealth | None:
        with self._lock:
            h = self._providers.get(provider)
            if h is None:
                return None
            return ProviderHealth(
                provider_name=h.provider_name,
                available=h.available,
                consecutive_failures=h.consecutive_failures,
                total_successes=h.total_successes,
                total_failures=h.total_failures,
                last_success=h.last_success,
                last_failure=h.last_failure,
                circuit_state=h.circuit_state,
                rate_limit_events=h.rate_limit_events,
                latencies=list(h.latencies),
                quota_remaining_requests=h.quota_remaining_requests,
                quota_remaining_tokens=h.quota_remaining_tokens,
                health_timestamp=h.health_timestamp,
            )

    def get_all(self) -> dict[str, ProviderHealth]:
        result = {}
        with self._lock:
            for name in self._providers:
                result[name] = self.get_health(name)  # type: ignore[assignment]
        return result

    def get_latency_percentiles(
        self, provider: str
    ) -> dict[str, float | None]:
        """Return P50/P95/P99 latency for a provider, or None if insufficient data."""
        with self._lock:
            h = self._providers.get(provider)
            if not h or len(h.latencies) < 2:
                return {"p50": None, "p95": None, "p99": None}
            sorted_lat = sorted(h.latencies)
            n = len(sorted_lat)
            return {
                "p50": sorted_lat[n // 2],
                "p95": sorted_lat[int(n * 0.95)],
                "p99": sorted_lat[int(n * 0.99)],
            }
