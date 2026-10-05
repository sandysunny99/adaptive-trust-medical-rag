from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol

from adaptive_trust_medical_rag.common.model_result import ModelExecutionError


@dataclass
class ProviderResponse:
    provider: str
    model: str
    request_id: str
    content: str
    structured_output: Optional[Dict[str, Any]]
    usage: Dict[str, int]
    latency_ms: float
    finish_reason: str
    transport_status: int
    raw_metadata: Dict[str, Any]

class ProviderAdapter(Protocol):
    def initialize(self) -> None:
        ...

    async def health_check(self) -> bool:
        ...

    async def generate(self, prompt: str) -> ProviderResponse:
        ...

    async def generate_structured(self, prompt: str, response_format: Dict[str, Any]) -> ProviderResponse:
        ...

    async def stream(self, prompt: str) -> Any:
        ...

    def normalize_error(self, error: Exception) -> ModelExecutionError:
        ...

    def get_model_metadata(self) -> Dict[str, Any]:
        ...
