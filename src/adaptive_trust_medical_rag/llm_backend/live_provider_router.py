import logging
from typing import Any, Dict, Optional

from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_backend.interfaces import ProviderAdapter, ProviderResponse
from adaptive_trust_medical_rag.llm_routing.types import FailureClass

log = logging.getLogger(__name__)

class LiveProviderRouter:
    def __init__(self, provider_priority: list[str] = None):
        self.provider_priority = provider_priority or []
        self.providers: Dict[str, ProviderAdapter] = {}

    def register_provider(self, name: str, adapter: ProviderAdapter) -> None:
        self.providers[name] = adapter

    async def generate_structured(self, prompt: str, response_format: Dict[str, Any]) -> ProviderResponse:
        providers_to_try = self.provider_priority if self.provider_priority else list(self.providers.keys())

        last_error = None
        for provider_name in providers_to_try:
            if provider_name not in self.providers:
                log.warning(f"Provider {provider_name} not registered in LiveProviderRouter")
                continue

            adapter = self.providers[provider_name]
            try:
                log.info(f"Attempting generation with provider: {provider_name}")
                response = await adapter.generate_structured(prompt, response_format)
                return response
            except ModelExecutionError as e:
                last_error = e
                # Fallback only for true transport/provider failures
                if getattr(e, "failure_class", FailureClass.UNKNOWN) not in [
                    FailureClass.TIMEOUT,
                    FailureClass.TRANSIENT_PROVIDER,
                    FailureClass.AUTHENTICATION,
                    FailureClass.RATE_LIMIT,
                    FailureClass.NETWORK
                ]:
                    log.error(f"Provider {provider_name} failed with non-transport error, not failing over. Error: {e}")
                    raise e

                log.warning(f"Provider {provider_name} failed with transport error {e}, attempting failover if configured.")

        if last_error:
            raise last_error

        raise ModelExecutionError("No providers available", status_code="NO_PROVIDERS")
