import time
import json
import httpx
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_backend.interfaces import ProviderAdapter, ProviderResponse
from adaptive_trust_medical_rag.llm_routing.types import FailureClass

class OpenAICompatibleBackend(ProviderAdapter):
    def __init__(self, provider_name: str, base_url: str, api_key: str, model_name: str, max_tokens: Optional[int] = None):
        self.provider_name = provider_name
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def initialize(self) -> None:
        pass

    async def health_check(self) -> bool:
        # A lightweight request to check models endpoint
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{self.base_url}/models", headers=self.headers, timeout=5.0)
                return resp.status_code == 200
            except Exception:
                return False

    async def generate(self, prompt: str) -> ProviderResponse:
        return await self._execute(prompt, None)

    async def generate_structured(self, prompt: str, response_format: Dict[str, Any]) -> ProviderResponse:
        return await self._execute(prompt, response_format)

    async def _execute(self, prompt: str, response_format: Optional[Dict[str, Any]]) -> ProviderResponse:
        t0 = time.perf_counter()
        
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        }
        if self.max_tokens is not None:
            payload["max_tokens"] = self.max_tokens
        if response_format is not None:
            payload["response_format"] = response_format

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
        except httpx.TimeoutException as e:
            raise self.normalize_error(e, "TIMEOUT")
        except Exception as e:
            raise self.normalize_error(e, "NETWORK_ERROR")

        if response.status_code != 200:
            raise self.normalize_error(Exception(response.text), str(response.status_code))

        latency_ms = (time.perf_counter() - t0) * 1000.0
        data = response.json()
        
        choices = data.get("choices", [])
        if not choices:
            raise ModelExecutionError(f"Empty response from {self.provider_name}", status_code="EMPTY_RESPONSE")
        
        message = choices[0].get("message", {})
        content = message.get("content", "")
        
        structured = None
        if response_format:
            try:
                structured = json.loads(content)
            except Exception:
                pass
        
        usage = data.get("usage", {})
        
        return ProviderResponse(
            provider=self.provider_name,
            model=self.model_name,
            request_id=data.get("id", ""),
            content=content,
            structured_output=structured,
            usage=usage,
            latency_ms=latency_ms,
            finish_reason=choices[0].get("finish_reason", ""),
            transport_status=response.status_code,
            raw_metadata=data
        )

    async def stream(self, prompt: str) -> Any:
        raise NotImplementedError("Streaming not yet implemented")

    def normalize_error(self, error: Exception, status_code: str = "") -> ModelExecutionError:
        error_msg = str(error).lower()
        if status_code == "401" or status_code == "403" or "unauthorized" in error_msg:
            err = ModelExecutionError(f"{self.provider_name} auth error: {error}", status_code=status_code)
            err.failure_class = FailureClass.AUTHENTICATION
            return err
        if status_code == "429" or "rate limit" in error_msg:
            err = ModelExecutionError(f"{self.provider_name} rate limit: {error}", status_code=status_code)
            err.failure_class = FailureClass.RATE_LIMIT
            return err
        if status_code == "TIMEOUT" or "timeout" in error_msg:
            err = ModelExecutionError(f"{self.provider_name} timeout: {error}", status_code=status_code)
            err.failure_class = FailureClass.TIMEOUT
            return err
        if status_code.startswith("5"):
            err = ModelExecutionError(f"{self.provider_name} server error: {error}", status_code=status_code)
            err.failure_class = FailureClass.TRANSIENT_PROVIDER
            return err
            
        err = ModelExecutionError(f"{self.provider_name} error: {error}", status_code=status_code)
        err.failure_class = FailureClass.UNKNOWN
        return err

    def get_model_metadata(self) -> Dict[str, Any]:
        return {"provider": self.provider_name, "model": self.model_name}
