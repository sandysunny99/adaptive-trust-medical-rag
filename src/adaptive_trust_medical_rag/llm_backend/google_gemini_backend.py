import asyncio
import time
import uuid
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from google import genai
from google.genai.errors import APIError

from adaptive_trust_medical_rag.common.model_result import (
    ModelExecutionError,
    ModelGenerationResult,
)


class GoogleGeminiBackend:
    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        self.client = genai.Client(api_key=self.api_key)
        self.last_rate_limit_info = None

    async def generate(self, prompt: str) -> ModelGenerationResult:
        request_started_at = datetime.now(timezone.utc).isoformat()
        t0 = time.perf_counter()

        response: Any = None
        try:
            # 30s strict timeout using asyncio.wait_for.
            # Do not retry on timeout.
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                ),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            raise ModelExecutionError(
                "Gemini API request timed out", status_code="TIMEOUT"
            ) from None
        except APIError as e:
            raise ModelExecutionError(
                f"Gemini API error: {e}", status_code=str(e.code)
            ) from e
        except Exception as e:
            raise ModelExecutionError(
                f"Unexpected error: {e}", status_code="INTERNAL_ERROR"
            ) from e

        response_received_at = datetime.now(timezone.utc).isoformat()
        t1 = time.perf_counter()

        if not response or not response.text:
            raise ModelExecutionError(
                "Empty response from Gemini API", status_code="EMPTY_RESPONSE"
            )

        response_text = response.text

        input_tokens = None
        output_tokens = None
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            input_tokens = getattr(response.usage_metadata, "prompt_token_count", None)
            output_tokens = getattr(response.usage_metadata, "candidates_token_count", None)

        provider_response_id = getattr(response, "response_id", None)

        # Determine finish reason if exposed
        finish_reason = None
        if hasattr(response, "candidates") and response.candidates:
            if hasattr(response.candidates[0], "finish_reason"):
                # Use str() in case it's an enum
                fr = response.candidates[0].finish_reason
                finish_reason = str(fr.name) if hasattr(fr, "name") else str(fr)

        ms = round((t1 - t0) * 1000, 3)

        return ModelGenerationResult(
            provider="gemini",
            model=self.model_name,
            local_execution_id=str(uuid.uuid4()),
            request_id=None,
            response_id=provider_response_id,
            request_started_at=request_started_at,
            response_received_at=response_received_at,
            finish_reason=finish_reason,
            response_text=response_text,
            response_hash=sha256(response_text.encode("utf-8")).hexdigest(),
            response_length=len(response_text),
            response_preview=response_text[:100],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            provider_call_latency_ms=ms,
            network_latency_ms=None,
            generation_latency_ms=None,
            total_generation_latency_ms=None,
            status="SUCCESS",
        )
