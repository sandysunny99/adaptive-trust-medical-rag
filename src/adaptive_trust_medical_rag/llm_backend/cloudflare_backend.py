"""Cloudflare Workers AI LLM backend adapter.

Uses the Cloudflare REST API (OpenAI-compatible chat completions endpoint).
Credential: CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID — never logged, never committed.
Free allocation: 10,000 Neurons/day on Workers Free plan (not unlimited).
"""
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


class CloudflareBackend:
    """Single-attempt Cloudflare Workers AI backend. Retry is handled by the router."""

    ENDPOINT_TEMPLATE = (
        "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/chat/completions"
    )

    def __init__(
        self,
        api_token: str,
        account_id: str,
        model_name: str = "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    ):
        # Store credentials for request construction — never expose in logs/repr
        self._api_token = api_token
        self._account_id = account_id
        self.model_name = model_name
        self._endpoint = self.ENDPOINT_TEMPLATE.format(account_id=account_id)

    def __repr__(self) -> str:
        return (
            f"CloudflareBackend(model={self.model_name}, "
            f"credential_present={bool(self._api_token)}, "
            f"account_configured={bool(self._account_id)})"
        )

    async def generate(self, prompt: str) -> ModelGenerationResult:
        request_started_at = datetime.now(timezone.utc).isoformat()
        t0 = time.perf_counter()

        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
        }

        response: Any = None
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self._endpoint, headers=headers, json=payload, timeout=60.0
                )
            except httpx.TimeoutException:
                raise ModelExecutionError(
                    "Cloudflare Workers AI request timed out",
                    status_code="TIMEOUT",
                ) from None
            except Exception as e:
                raise ModelExecutionError(
                    f"Cloudflare network error: {e}",
                    status_code="NETWORK_ERROR",
                ) from e

        t1 = time.perf_counter()
        response_received_at = datetime.now(timezone.utc).isoformat()

        # Extract rate-limit info (Cloudflare may not expose standard headers)
        from adaptive_trust_medical_rag.llm_routing.types import RateLimitInfo
        rate_limit_info = None
        if response is not None:
            try:
                rate_limit_info = RateLimitInfo(
                    remaining_requests=None,  # Cloudflare uses Neuron-based quota
                    remaining_tokens=None,
                    retry_after=float(response.headers.get("retry-after", 0)) or None,
                )
            except Exception:
                pass  # nosec B110

        if response.status_code != 200:
            error_msg = f"Cloudflare Workers AI error (status {response.status_code})"
            try:
                error_data = response.json()
                if "errors" in error_data and error_data["errors"]:
                    error_msg += f": {error_data['errors'][0].get('message', '')}"
            except Exception:
                pass  # nosec B110

            if response.status_code == 401:
                raise ModelExecutionError(error_msg, status_code="401") from None
            if response.status_code == 429:
                raise ModelExecutionError(error_msg, status_code="429") from None
            raise ModelExecutionError(error_msg, status_code=str(response.status_code))

        data = response.json()

        # OpenAI-compatible response format
        choices = data.get("choices", [])
        if not choices:
            # Cloudflare native format fallback
            result_obj = data.get("result", {})
            response_text = result_obj.get("response", "")
        else:
            message = choices[0].get("message", {})
            response_text = message.get("content", "")

        if not response_text:
            raise ModelExecutionError(
                "Empty response from Cloudflare Workers AI",
                status_code="EMPTY_RESPONSE",
            )

        ms = round((t1 - t0) * 1000, 3)

        # Token usage (if available)
        input_tokens = None
        output_tokens = None
        usage = data.get("usage", {})
        if usage:
            input_tokens = usage.get("prompt_tokens")
            output_tokens = usage.get("completion_tokens")

        return ModelGenerationResult(
            provider="cloudflare",
            model=self.model_name,
            local_execution_id=str(uuid.uuid4()),
            request_id=None,
            response_id=data.get("id"),
            request_started_at=request_started_at,
            response_received_at=response_received_at,
            finish_reason=choices[0].get("finish_reason") if choices else "stop",
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
