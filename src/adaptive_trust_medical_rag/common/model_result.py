# Shared model result types for LLM backends

from dataclasses import dataclass
from typing import Any

class ModelExecutionError(Exception):
    """Raised when external LLM execution fails or returns an invalid/empty response."""

    def __init__(self, message: str, status_code: str = "FAILED_MODEL_EXECUTION") -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class ModelGenerationResult:
    provider: str
    model: str
    local_execution_id: str
    request_id: str | None
    response_id: str | None
    request_started_at: str
    response_received_at: str
    finish_reason: str | None
    response_text: str
    response_hash: str
    response_length: int
    response_preview: str
    input_tokens: int | None
    output_tokens: int | None
    provider_call_latency_ms: float
    network_latency_ms: float | None = None
    generation_latency_ms: float | None = None
    total_generation_latency_ms: float | None = None
    status: str = "SUCCESS"
    rate_limit: Any | None = None

    @property
    def latency_ms(self) -> float:
        return self.provider_call_latency_ms
