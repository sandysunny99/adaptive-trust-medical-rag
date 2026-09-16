"""LLM Provider Router — availability-only routing with retry, circuit breaking, and failover."""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_routing.circuit_breaker import CircuitBreaker
from adaptive_trust_medical_rag.llm_routing.config import ProviderConfig, RoutingConfig
from adaptive_trust_medical_rag.llm_routing.health import ProviderHealthRegistry
from adaptive_trust_medical_rag.llm_routing.retry import RetryPolicy
from adaptive_trust_medical_rag.llm_routing.types import (
    AllProvidersUnavailableError,
    CircuitState,
    ExperimentProviderUnavailable,
    FailureClass,
    FAILOVER_ELIGIBLE,
    ProviderAttemptResult,
    RateLimitInfo,
    RoutingMode,
)

logger = logging.getLogger(__name__)

class LLMProviderRouter:
    """LLM Provider Router with availability-only routing, retry, circuit breaking, and failover."""

    def __init__(self, config: RoutingConfig, backends: dict[str, Any]) -> None:
        self.config = config
        self.backends = backends
        self.providers_by_name = {p.name: p for p in config.providers}
        self.circuit_breakers = {}
        if config.circuit_breaker_enabled:
            for p in config.providers:
                self.circuit_breakers[p.name] = CircuitBreaker(
                    provider_name=p.name,
                    failure_threshold=config.circuit_breaker_threshold,
                    recovery_timeout_seconds=config.circuit_breaker_recovery_seconds
                )
        self.health_registry = ProviderHealthRegistry()

    async def generate(self, prompt: str, case_id: str | None = None) -> ProviderAttemptResult:
        is_scientific = self.config.mode == RoutingMode.SCIENTIFIC
        
        # Build eligible provider list
        providers_to_try = []
        for p in self.config.providers:
            # In scientific mode, only the first (frozen) provider is allowed
            if is_scientific:
                providers_to_try = [p.name]
                break
            # Filter out tertiary providers (priority >= 3) unless enabled
            if p.priority >= 3 and not self.config.tertiary_enabled:
                continue
            providers_to_try.append(p.name)
            
        if not providers_to_try:
            raise AllProvidersUnavailableError([])

        for provider_name in providers_to_try:
            if provider_name not in self.backends or provider_name not in self.providers_by_name:
                logger.warning(f"Provider {provider_name} not properly configured")
                continue

            provider_config = self.providers_by_name[provider_name]
            circuit_breaker = self.circuit_breakers.get(provider_name)
            backend = self.backends[provider_name]
            retry_policy = RetryPolicy(
                self.config.retry_base_delay, 
                self.config.retry_max_delay, 
                self.config.retry_jitter
            )
            
            if circuit_breaker and circuit_breaker.state == CircuitState.OPEN:
                logger.warning(f"Skipping {provider_name}, circuit is OPEN.")
                continue

            attempt_num = 1
            max_attempts = self.config.retry_max_attempts + 1

            while attempt_num <= max_attempts:
                start_time = time.monotonic()
                try:
                    result = await backend.generate(prompt)
                    
                    latency = time.monotonic() - start_time
                    
                    rate_limit = getattr(result, "rate_limit", None)
                    if not isinstance(rate_limit, RateLimitInfo):
                        rate_limit = None
                        
                    self.health_registry.record_success(provider_name, latency)
                    if circuit_breaker:
                        circuit_breaker.record_success()
                        
                    logger.info(f"Attempt {attempt_num} for {provider_name} succeeded in {latency:.2f}s")
                    
                    expected_prov = self.config.providers[0].name if self.config.providers else None
                    expected_mod = self.providers_by_name[expected_prov].model_id if expected_prov in self.providers_by_name else None
                    actual_mod = getattr(result, "model", None)
                    
                    return ProviderAttemptResult(
                        provider=provider_name,
                        model=actual_mod or "",
                        request_id=getattr(result, "request_id", "") or "",
                        start_time=getattr(result, "request_started_at", datetime.now(UTC).isoformat()),
                        end_time=getattr(result, "response_received_at", datetime.now(UTC).isoformat()),
                        success=True,
                        content=result.response_text if hasattr(result, "response_text") else getattr(result, "content", ""),
                        latency_ms=int(latency * 1000),
                        retry_attempt=attempt_num,
                        rate_limit_info=rate_limit,
                        expected_provider=expected_prov,
                        actual_provider=provider_name,
                        expected_model=expected_mod,
                        actual_model=actual_mod,
                        provider_match=(provider_name == expected_prov),
                        experimental_mode=self.config.mode
                    )
                    
                except Exception as e:
                    latency = time.monotonic() - start_time
                    error_msg = str(e)
                    
                    failure_class = getattr(e, "failure_class", FailureClass.UNKNOWN)
                    
                    # Fallback classification if not explicitly marked
                    if failure_class == FailureClass.UNKNOWN:
                        lower_msg = error_msg.lower()
                        if "rate limit" in lower_msg or "429" in error_msg:
                            failure_class = FailureClass.RATE_LIMIT
                        elif "timeout" in lower_msg:
                            failure_class = FailureClass.TIMEOUT
                        elif "unauthorized" in lower_msg or "401" in error_msg or "403" in error_msg:
                            failure_class = FailureClass.AUTHENTICATION
                        elif "validation" in lower_msg or "400" in error_msg:
                            failure_class = FailureClass.INVALID_REQUEST
                        elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                            failure_class = FailureClass.TRANSIENT_PROVIDER
                            
                    self.health_registry.record_failure(provider_name, failure_class)
                    if circuit_breaker:
                        circuit_breaker.record_failure(failure_class)
                        
                    logger.warning(f"Attempt {attempt_num} for {provider_name} failed: {error_msg}")
                    
                    if failure_class not in FAILOVER_ELIGIBLE:
                        # Non-transient error, raise immediately without retry or failover
                        raise ModelExecutionError(f"Non-transient error from {provider_name}: {error_msg}") from e
                    
                    if attempt_num < max_attempts:
                        delay = retry_policy.get_delay(attempt_num)
                        logger.info(f"Retrying {provider_name} in {delay:.2f}s")
                        time.sleep(delay)
                        attempt_num += 1
                    else:
                        logger.error(f"Exhausted retries for {provider_name}")
                        break
                    
            if not is_scientific:
                # In non-scientific mode, we just break out of this provider loop if it fails, and move to next
                pass

        # Exhausted all providers
        if is_scientific:
            raise ExperimentProviderUnavailable(
                case_id=case_id,
                intended_provider=providers_to_try[0],
                intended_model=self.providers_by_name[providers_to_try[0]].model_id if providers_to_try[0] in self.providers_by_name else "unknown",
                failure_reason=f"Exhausted retries. Last error: {error_msg if 'error_msg' in locals() else 'Unknown'}",
                retry_count=locals().get('max_attempts', 0)
            )
        else:
            raise AllProvidersUnavailableError([])
