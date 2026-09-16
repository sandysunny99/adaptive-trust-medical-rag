"""Hugging Face Inference Providers LLM backend adapter.

Uses huggingface_hub.InferenceClient for text generation.
Credential: HF_TOKEN environment variable — never logged, never committed.
This is a DEVELOPMENT_FALLBACK provider, not a guaranteed free-tier backend.
"""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from adaptive_trust_medical_rag.common.model_result import (
    ModelExecutionError,
    ModelGenerationResult,
)


class HuggingFaceBackend:
    """Single-attempt HF Inference backend. Retry is handled by the router."""

    def __init__(self, token: str, model_name: str = "meta-llama/Llama-3.3-70B-Instruct"):
        # Store token for InferenceClient init — never expose in logs/repr
        self._token = token
        self.model_name = model_name

    def __repr__(self) -> str:
        return f"HuggingFaceBackend(model={self.model_name}, credential_present={bool(self._token)})"

    async def generate(self, prompt: str) -> ModelGenerationResult:
        from huggingface_hub import InferenceClient

        request_started_at = datetime.now(timezone.utc).isoformat()
        t0 = time.perf_counter()

        try:
            client = InferenceClient(model=self.model_name, token=self._token)
            response_text = client.text_generation(
                prompt,
                max_new_tokens=2048,
                details=False,
            )
        except Exception as e:
            error_msg = str(e)
            # Classify the error without exposing the token
            if "401" in error_msg or "unauthorized" in error_msg.lower():
                raise ModelExecutionError(
                    f"HuggingFace authentication failure for model {self.model_name}",
                    status_code="401",
                ) from e
            if "429" in error_msg or "rate" in error_msg.lower():
                raise ModelExecutionError(
                    f"HuggingFace rate limit for model {self.model_name}",
                    status_code="429",
                ) from e
            raise ModelExecutionError(
                f"HuggingFace error for {self.model_name}: {error_msg}",
                status_code="INTERNAL_ERROR",
            ) from e

        t1 = time.perf_counter()
        response_received_at = datetime.now(timezone.utc).isoformat()

        if not response_text:
            raise ModelExecutionError(
                "Empty response from HuggingFace Inference",
                status_code="EMPTY_RESPONSE",
            )

        ms = round((t1 - t0) * 1000, 3)

        return ModelGenerationResult(
            provider="huggingface",
            model=self.model_name,
            local_execution_id=str(uuid.uuid4()),
            request_id=None,
            response_id=None,
            request_started_at=request_started_at,
            response_received_at=response_received_at,
            finish_reason="stop",
            response_text=response_text,
            response_hash=sha256(response_text.encode("utf-8")).hexdigest(),
            response_length=len(response_text),
            response_preview=response_text[:100],
            input_tokens=None,  # HF text_generation does not always return token counts
            output_tokens=None,
            provider_call_latency_ms=ms,
            network_latency_ms=None,
            generation_latency_ms=None,
            total_generation_latency_ms=None,
            status="SUCCESS",
            rate_limit=None,  # HF Inference does not expose rate-limit headers consistently
        )
