import uuid
from datetime import datetime, timezone
from hashlib import sha256

from adaptive_trust_medical_rag.common.model_result import ModelGenerationResult


class MockLLMBackend:
    """Mock backend for deterministic tests, matching legacy LiveModelAdapter output."""

    async def generate(self, prompt: str) -> ModelGenerationResult:
        request_started_at = datetime.now(timezone.utc).isoformat()

        response_text = f"Evidence-grounded response for query context: {prompt[:150]}..."

        response_received_at = datetime.now(timezone.utc).isoformat()

        return ModelGenerationResult(
            provider="mock",
            model="deterministic-mock",
            local_execution_id=str(uuid.uuid4()),
            request_id=None,
            response_id=None,
            request_started_at=request_started_at,
            response_received_at=response_received_at,
            finish_reason=None,
            response_text=response_text,
            response_hash=sha256(response_text.encode("utf-8")).hexdigest(),
            response_length=len(response_text),
            response_preview=response_text[:100],
            input_tokens=None,
            output_tokens=None,
            provider_call_latency_ms=0.0,
            network_latency_ms=None,
            generation_latency_ms=None,
            total_generation_latency_ms=None,
            status="SUCCESS",
        )
