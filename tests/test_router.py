import pytest
import asyncio
from datetime import datetime, UTC
from typing import Any

from adaptive_trust_medical_rag.llm_routing.router import LLMProviderRouter
from adaptive_trust_medical_rag.llm_routing.config import RoutingConfig, ProviderConfig
from adaptive_trust_medical_rag.llm_routing.types import (
    RoutingMode,
    FailureClass,
    CircuitState,
    AllProvidersUnavailableError,
    ExperimentProviderUnavailable
)
from adaptive_trust_medical_rag.common.model_result import (
    ModelGenerationResult,
    ModelExecutionError
)

class DummyBackend:
    def __init__(self, provider_name: str, should_fail: bool = False, failure_class: FailureClass = FailureClass.TIMEOUT):
        self.provider_name = provider_name
        self.should_fail = should_fail
        self.failure_class = failure_class
        self.calls = 0

    async def generate(self, prompt: str) -> ModelGenerationResult:
        self.calls += 1
        if self.should_fail:
            err = ModelExecutionError(f"Mock failure from {self.provider_name}")
            err.failure_class = self.failure_class
            raise err
        return ModelGenerationResult(
            provider=self.provider_name,
            model="mock_model",
            local_execution_id="mock",
            request_id="mock",
            response_id="mock",
            request_started_at=datetime.now(UTC).isoformat(),
            response_received_at=datetime.now(UTC).isoformat(),
            finish_reason="stop",
            response_text=f"Hello from {self.provider_name}",
            response_hash="hash",
            response_length=5,
            response_preview="Hello",
            input_tokens=10,
            output_tokens=10,
            provider_call_latency_ms=10.0,
            status="SUCCESS"
        )


@pytest.fixture
def mock_backends():
    return {
        "primary": DummyBackend("primary"),
        "secondary": DummyBackend("secondary")
    }

@pytest.fixture
def routing_config():
    return RoutingConfig(
        mode=RoutingMode.APPLICATION,
        providers=[
            ProviderConfig("primary", 1, "mock_model", "KEY"),
            ProviderConfig("secondary", 2, "mock_model", "KEY")
        ],
        retry_max_attempts=1,
        retry_base_delay=0.01,
        circuit_breaker_threshold=2
    )

@pytest.mark.asyncio
async def test_router_success(routing_config, mock_backends):
    router = LLMProviderRouter(config=routing_config, backends=mock_backends)
    result = await router.generate("test prompt")
    assert result.success
    assert result.provider == "primary"
    assert result.expected_provider == "primary"
    assert result.provider_match is True
    assert mock_backends["primary"].calls == 1
    assert mock_backends["secondary"].calls == 0

@pytest.mark.asyncio
async def test_router_failover_to_secondary(routing_config, mock_backends):
    mock_backends["primary"].should_fail = True
    # Primary will fail twice (initial + 1 retry) then router failover to secondary
    router = LLMProviderRouter(config=routing_config, backends=mock_backends)
    result = await router.generate("test prompt")
    
    assert result.success
    assert result.provider == "secondary"
    assert result.expected_provider == "primary"
    assert result.provider_match is False
    assert mock_backends["primary"].calls == 2
    assert mock_backends["secondary"].calls == 1

@pytest.mark.asyncio
async def test_circuit_breaker_opens(routing_config, mock_backends):
    mock_backends["primary"].should_fail = True
    router = LLMProviderRouter(config=routing_config, backends=mock_backends)
    
    # First call - primary fails 2 times (initial + 1 retry). Circuit breaker threshold is 2!
    # Primary circuit breaker should now be OPEN.
    await router.generate("test prompt")
    assert router.circuit_breakers["primary"].state == CircuitState.OPEN
    
    # Second call - should skip primary instantly and use secondary
    mock_backends["primary"].calls = 0
    mock_backends["secondary"].calls = 0
    await router.generate("test prompt")
    
    assert mock_backends["primary"].calls == 0
    assert mock_backends["secondary"].calls == 1

@pytest.mark.asyncio
async def test_scientific_mode_no_failover(routing_config, mock_backends):
    routing_config.mode = RoutingMode.SCIENTIFIC
    mock_backends["primary"].should_fail = True
    
    router = LLMProviderRouter(config=routing_config, backends=mock_backends)
    
    # Scientific mode should NOT failover. If primary fails, it throws ExperimentProviderUnavailable
    with pytest.raises(ExperimentProviderUnavailable):
        await router.generate("test prompt")
    
    assert mock_backends["primary"].calls == 2
    assert mock_backends["secondary"].calls == 0
