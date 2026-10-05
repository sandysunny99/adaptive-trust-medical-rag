from __future__ import annotations

import enum
from dataclasses import dataclass, field


class FailureClass(str, enum.Enum):
    """Classified failure types for retry/failover decisions."""
    TRANSIENT_PROVIDER = "TRANSIENT_PROVIDER"  # 502, 503
    RATE_LIMIT = "RATE_LIMIT"                  # 429
    TIMEOUT = "TIMEOUT"                        # request timeout
    CAPACITY = "CAPACITY"                      # provider overload
    NETWORK = "NETWORK"                        # connection error
    AUTHENTICATION = "AUTHENTICATION"          # 401
    AUTHORIZATION = "AUTHORIZATION"            # 403
    INVALID_REQUEST = "INVALID_REQUEST"        # 400
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"        # invalid model ID
    SCHEMA_ERROR = "SCHEMA_ERROR"              # structured output schema failure
    APPLICATION_SEMANTIC = "APPLICATION_SEMANTIC"  # security block, claim failure, etc.
    UNKNOWN = "UNKNOWN"


# Define which failure classes are eligible for retry/failover
FAILOVER_ELIGIBLE = frozenset({
    FailureClass.TRANSIENT_PROVIDER,
    FailureClass.RATE_LIMIT,
    FailureClass.TIMEOUT,
    FailureClass.CAPACITY,
    FailureClass.NETWORK,
})


class CircuitState(str, enum.Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class RoutingMode(str, enum.Enum):
    APPLICATION = "APPLICATION"
    DEVELOPMENT = "DEVELOPMENT"
    SCIENTIFIC = "SCIENTIFIC"


class FreeTierPolicy(str, enum.Enum):
    """Free-tier cost classification for a provider route."""
    FREE_CONFIRMED = "FREE_CONFIRMED"
    FREE_UNKNOWN = "FREE_UNKNOWN"
    PAID_REQUIRED = "PAID_REQUIRED"
    QUOTA_EXHAUSTED = "QUOTA_EXHAUSTED"


@dataclass
class RateLimitInfo:
    """Provider-neutral rate limit metadata."""
    limit_requests: int | None = None
    remaining_requests: int | None = None
    reset_requests: str | None = None  # ISO timestamp or seconds
    limit_tokens: int | None = None
    remaining_tokens: int | None = None
    reset_tokens: str | None = None
    retry_after: float | None = None  # seconds


@dataclass
class ProviderAttemptResult:
    """Rich internal result from a single provider generation attempt."""
    content: str
    provider: str
    model: str
    request_id: str
    start_time: str  # ISO timestamp
    end_time: str    # ISO timestamp
    latency_ms: float
    input_tokens: int | None = None
    output_tokens: int | None = None
    status_code: str | None = None
    retry_after: float | None = None
    failure_class: FailureClass | None = None
    retry_attempt: int = 0
    circuit_state: CircuitState = CircuitState.CLOSED
    failover_trigger: str | None = None
    structured_output_valid: bool | None = None
    experimental_mode: RoutingMode = RoutingMode.APPLICATION
    rate_limit_info: RateLimitInfo | None = None
    success: bool = True
    error_message: str | None = None
    expected_provider: str | None = None
    actual_provider: str | None = None
    expected_model: str | None = None
    actual_model: str | None = None
    provider_match: bool | None = None


@dataclass
class ProviderHealth:
    """Health state for a single provider."""
    provider_name: str
    available: bool = True
    consecutive_failures: int = 0
    total_successes: int = 0
    total_failures: int = 0
    last_success: str | None = None
    last_failure: str | None = None
    circuit_state: CircuitState = CircuitState.CLOSED
    rate_limit_events: int = 0
    latencies: list[float] = field(default_factory=list)  # recent latencies in ms
    quota_remaining_requests: int | None = None
    quota_remaining_tokens: int | None = None
    health_timestamp: str | None = None
    credential_state: str | None = None  # "PRESENT" / "MISSING" / "INVALID"
    free_tier_policy: FreeTierPolicy | None = None


class AllProvidersUnavailableError(Exception):
    """Raised when all configured providers are exhausted."""
    def __init__(self, attempts: list[ProviderAttemptResult]):
        self.attempts = attempts
        providers = [a.provider for a in attempts]
        super().__init__(f"All providers unavailable: {providers}")


class ExperimentProviderUnavailable(Exception):
    """Raised in SCIENTIFIC mode when the frozen provider is unavailable."""
    def __init__(
        self,
        case_id: str | None,
        intended_provider: str,
        intended_model: str,
        failure_reason: str,
        retry_count: int,
        configuration_hash: str | None = None,
    ):
        self.case_id = case_id
        self.intended_provider = intended_provider
        self.intended_model = intended_model
        self.failure_reason = failure_reason
        self.retry_count = retry_count
        self.configuration_hash = configuration_hash
        super().__init__(
            f"Scientific mode: {intended_provider}/{intended_model} unavailable "
            f"after {retry_count} attempts: {failure_reason}"
        )
