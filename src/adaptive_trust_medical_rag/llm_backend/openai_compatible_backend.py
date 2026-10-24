import json
import logging
import time
from typing import Any, Dict, Optional

import httpx

from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_backend.interfaces import ProviderAdapter, ProviderResponse
from adaptive_trust_medical_rag.llm_backend.provider_errors import classify_provider_error
from adaptive_trust_medical_rag.llm_routing.types import FailureClass

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT_S = 30.0


def _retry_after(headers: Any) -> float | None:
    try:
        value = float(headers.get("retry-after")) if headers is not None else None
    except (TypeError, ValueError):
        return None
    return value if value is not None and value >= 0 else None


class OpenAICompatibleBackend(ProviderAdapter):
    def __init__(self, provider_name: str, base_url: str, api_key: str, model_name: str,
                 max_tokens: Optional[int] = None, timeout_s: float = DEFAULT_TIMEOUT_S):
        self.provider_name = provider_name
        self.timeout_s = timeout_s
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def initialize(self) -> None:
                pass  # nosec B110

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
                    timeout=httpx.Timeout(self.timeout_s, connect=min(10.0, self.timeout_s)),
                )
        except httpx.TimeoutException as e:
            raise self.normalize_error(e, "TIMEOUT")
        except Exception as e:
            raise self.normalize_error(e, "NETWORK_ERROR")

        if response.status_code != 200:
            err = self.normalize_error(Exception(response.text), str(response.status_code))
            err.retry_after = _retry_after(getattr(response, "headers", None))
            raise err

        latency_ms = (time.perf_counter() - t0) * 1000.0
        # A 200 whose body is not a chat completion is a malformed response (SCHEMA_ERROR), so it
        # reaches the router as a classified failure instead of escaping it as a raw exception.
        try:
            data = response.json()
        except ValueError:
            raise self._malformed("response body is not JSON")
        if not isinstance(data, dict):
            raise self._malformed("response body is not a JSON object")

        choices = data.get("choices", [])
        if not choices:
            err = ModelExecutionError(f"Empty response from {self.provider_name}", status_code="EMPTY_RESPONSE")
            err.failure_class = FailureClass.SCHEMA_ERROR
            raise err

        first = choices[0] if isinstance(choices, list) else None
        message = first.get("message") if isinstance(first, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise self._malformed("completion has no text content")

        structured = None
        if response_format:
            try:
                structured = json.loads(content)
            except json.JSONDecodeError:
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
            finish_reason=first.get("finish_reason", ""),
            transport_status=response.status_code,
            raw_metadata=data
        )

    def _malformed(self, what: str) -> ModelExecutionError:
        err = ModelExecutionError(f"{self.provider_name} invalid model output: {what}",
                                  status_code="MALFORMED_RESPONSE")
        err.failure_class = FailureClass.SCHEMA_ERROR
        err.provider = self.provider_name
        err.model = self.model_name
        return err

    async def stream(self, prompt: str) -> Any:
        raise NotImplementedError("Streaming not yet implemented")

    def normalize_error(self, error: Exception, status_code: str = "") -> ModelExecutionError:
        """Classify a provider failure with the shared classifier, adding provider-specific hints.

        A 404 is MODEL_NOT_FOUND: the model or the function behind it is not available to this
        account or endpoint. That is a configuration problem, so it is never retried, though another
        provider may be tried. Groq's 400 ``json_validate_failed`` means the model produced no valid
        JSON, a malformed response (SCHEMA_ERROR), not a malformed request.
        """
        body = str(error)  # read for the classification below only: it can echo the prompt
        if status_code in ("TIMEOUT", "NETWORK_ERROR"):
            classification = classify_provider_error(error)
        else:
            try:
                http_status = int(status_code)
            except ValueError:
                http_status = None
            classification = classify_provider_error(error, http_status)
        fc = classification.failure_class
        if status_code == "TIMEOUT":
            fc = FailureClass.TIMEOUT
        elif status_code == "NETWORK_ERROR" and fc == FailureClass.UNKNOWN:
            fc = FailureClass.NETWORK
        elif status_code == "400" and "json_validate_failed" in body:
            fc = FailureClass.SCHEMA_ERROR
        elif fc == FailureClass.UNKNOWN and status_code == "400":
            fc = FailureClass.INVALID_REQUEST

        label = {
            FailureClass.AUTHENTICATION: "auth error",
            FailureClass.AUTHORIZATION: "auth error",
            FailureClass.RATE_LIMIT: "rate limit",
            FailureClass.TIMEOUT: "timeout",
            FailureClass.TRANSIENT_PROVIDER: "server error",
            FailureClass.NETWORK: "network error",
            FailureClass.SCHEMA_ERROR: "invalid model output",
            FailureClass.INVALID_REQUEST: "invalid request",
        }.get(fc, "error")
        if fc == FailureClass.MODEL_NOT_FOUND:
            message = (f"{self.provider_name} model not found: model '{self.model_name}' is not available "
                       f"to this account or endpoint (HTTP {status_code}); check the configured model ID.")
        else:
            message = f"{self.provider_name} {label} (HTTP {status_code})"
        # The upstream body can echo the prompt or name the account; truncating or redacting it does not
        # make it safe, so only its size is logged.
        if body:
            log.warning("%s HTTP %s: %s (upstream body not logged, %d characters)",
                        self.provider_name, status_code, label, len(body))
        err = ModelExecutionError(message, status_code=status_code)
        err.failure_class = fc
        err.provider = self.provider_name
        err.model = self.model_name
        return err

    def get_model_metadata(self) -> Dict[str, Any]:
        return {"provider": self.provider_name, "model": self.model_name}
