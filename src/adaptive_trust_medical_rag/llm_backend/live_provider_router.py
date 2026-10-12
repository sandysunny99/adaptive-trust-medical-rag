import logging
from typing import Any, Dict, Optional

from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_backend.interfaces import ProviderAdapter, ProviderResponse
from adaptive_trust_medical_rag.llm_routing.types import FailureClass

log = logging.getLogger(__name__)

class LiveProviderRouter:
    def __init__(
        self,
        provider_priority: list[str] | None = None,
        primary_provider: str | None = None,
        secondary_provider: str | None = None,
    ):
        if provider_priority is not None:
            self.provider_priority = list(provider_priority)
        else:
            self.provider_priority = []
            if primary_provider:
                self.provider_priority.append(primary_provider)
            if secondary_provider and secondary_provider != primary_provider:
                self.provider_priority.append(secondary_provider)
        self.providers: Dict[str, ProviderAdapter] = {}

    def register_provider(self, name: str, adapter: ProviderAdapter) -> None:
        self.providers[name] = adapter

    async def generate_structured(
        self,
        prompt: str,
        response_format: Dict[str, Any],
        provider_name: str | None = None,
    ) -> ProviderResponse:
        # If a specific provider was requested by the user, route directly without fallback
        if provider_name:
            if provider_name not in self.providers:
                raise ModelExecutionError(
                    f"Requested LLM provider '{provider_name}' is not registered or configured.",
                    status_code="PROVIDER_NOT_FOUND",
                )
            log.info(f"Direct generation with user-selected provider: {provider_name}")
            return await self.providers[provider_name].generate_structured(prompt, response_format)

        providers_to_try = self.provider_priority if self.provider_priority else list(self.providers.keys())

        last_error = None
        for p_name in providers_to_try:
            if p_name not in self.providers:
                log.warning(f"Provider {p_name} not registered in LiveProviderRouter")
                continue

            adapter = self.providers[p_name]
            try:
                log.info(f"Attempting generation with provider: {p_name}")
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
                    log.error(f"Provider {p_name} failed with non-transport error, not failing over. Error: {e}")
                    raise e

                log.warning(f"Provider {p_name} failed with transport error {e}, attempting failover if configured.")

        if last_error:
            raise last_error

        raise ModelExecutionError("No providers available", status_code="NO_PROVIDERS")
