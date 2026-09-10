"""RoutedLLMBackend — adapts LLMProviderRouter to the orchestrator's LLMBackend protocol."""
from __future__ import annotations

from adaptive_trust_medical_rag.llm_routing.router import LLMProviderRouter
from typing import Any
from adaptive_trust_medical_rag.llm_routing.types import (
    AllProvidersUnavailableError,
    ExperimentProviderUnavailable,
    ProviderAttemptResult,
)


class RoutedLLMBackend:
    """Adapts LLMProviderRouter to the orchestrator's sync LLMBackend protocol.
    
    The orchestrator expects: generate(prompt: str) -> str
    This adapter wraps the router's rich ProviderAttemptResult and returns
    only the content string, preserving backward compatibility.
    
    The last attempt result is available via self.last_result for telemetry.
    """

    def __init__(self, router: LLMProviderRouter) -> None:
        self._router = router
        self.last_result: ProviderAttemptResult | None = None

    async def generate(self, prompt: str) -> Any:
        """Generate via the provider router. Returns a ModelGenerationResult."""
        from adaptive_trust_medical_rag.common.model_result import ModelGenerationResult
        import uuid
        from datetime import datetime, UTC
        import hashlib
        
        result = await self._router.generate(prompt)
        self.last_result = result
        
        return ModelGenerationResult(
            provider=result.actual_provider or result.provider,
            model=result.actual_model or result.model,
            local_execution_id=str(uuid.uuid4()),
            request_id=result.request_id,
            response_id=result.request_id,
            request_started_at=result.start_time,
            response_received_at=result.end_time,
            finish_reason="stop",
            response_text=result.content,
            response_hash=hashlib.sha256(result.content.encode("utf-8")).hexdigest(),
            response_length=len(result.content),
            response_preview=result.content[:100],
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            provider_call_latency_ms=result.latency_ms,
            status="SUCCESS",
            rate_limit=result.rate_limit_info
        )
