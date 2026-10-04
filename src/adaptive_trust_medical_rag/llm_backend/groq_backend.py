"""Groq LLM backend adapter using httpx (OpenAI-compatible API)."""
from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

import httpx

from adaptive_trust_medical_rag.common.model_result import (
    ModelExecutionError,
    ModelGenerationResult,
)

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqBackend:
    """Single-attempt Groq LLM backend. Retry is handled by the router."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "openai/gpt-oss-120b",
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.last_rate_limit_info = None

    async def generate(self, prompt: str, response_format: dict[str, str] | None = None) -> ModelGenerationResult:
        request_started_at = datetime.now(timezone.utc).isoformat()
        t0 = time.perf_counter()

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
        }
        if self.max_tokens is not None:
            payload["max_tokens"] = self.max_tokens
        if response_format is not None:
            payload["response_format"] = response_format
        
        response: Any = None
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    GROQ_API_URL, headers=headers, json=payload, timeout=30.0
                )
            except httpx.TimeoutException:
                raise ModelExecutionError("Groq API request timed out", status_code="TIMEOUT") from None
            except Exception as e:
                raise ModelExecutionError(f"Unexpected error: {e}", status_code="INTERNAL_ERROR") from e

        from adaptive_trust_medical_rag.llm_routing.types import RateLimitInfo
        
        # Extract rate limits
        rate_limit_info = None
        if response is not None:
            try:
                rate_limit_info = RateLimitInfo(
                    remaining_requests=int(response.headers.get("x-ratelimit-remaining-requests", 0)) or None,
                    remaining_tokens=int(response.headers.get("x-ratelimit-remaining-tokens", 0)) or None,
                    limit_requests=int(response.headers.get("x-ratelimit-limit-requests", 0)) or None,
                    limit_tokens=int(response.headers.get("x-ratelimit-limit-tokens", 0)) or None,
                    reset_requests=response.headers.get("x-ratelimit-reset-requests"),
                    reset_tokens=response.headers.get("x-ratelimit-reset-tokens"),
                    retry_after=float(response.headers.get("retry-after", 0)) or None,
                )
                self.last_rate_limit_info = rate_limit_info
            except Exception:
                pass  # nosec B110
            
        if response.status_code != 200:
            error_msg = f"Groq API error (status {response.status_code})"
            try:
                error_data = response.json()
                if "error" in error_data and "message" in error_data["error"]:
                    error_msg += f": {error_data['error']['message']}"
            except Exception:
                pass  # nosec B110
            raise ModelExecutionError(error_msg, status_code=str(response.status_code))

        response_received_at = datetime.now(timezone.utc).isoformat()
        t1 = time.perf_counter()

        data = response.json()
        
        choices = data.get("choices", [])
        if not choices:
            raise ModelExecutionError("Empty response from Groq API", status_code="EMPTY_RESPONSE")
            
        message = choices[0].get("message", {})
        response_text = message.get("content", "")
        
        if not response_text:
            raise ModelExecutionError("Empty content from Groq API", status_code="EMPTY_RESPONSE")

        input_tokens = None
        output_tokens = None
        usage = data.get("usage", {})
        if usage:
            input_tokens = usage.get("prompt_tokens")
            output_tokens = usage.get("completion_tokens")

        provider_response_id = data.get("id")
        finish_reason = choices[0].get("finish_reason")

        ms = round((t1 - t0) * 1000, 3)

        return ModelGenerationResult(
            provider="groq",
            model=self.model_name,
            local_execution_id=str(uuid.uuid4()),
            request_id=None,
            response_id=provider_response_id,
            request_started_at=request_started_at,
            response_received_at=response_received_at,
            finish_reason=str(finish_reason) if finish_reason else None,
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
            rate_limit=rate_limit_info,
        )
