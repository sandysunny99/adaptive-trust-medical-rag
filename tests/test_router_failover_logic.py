import pytest
from unittest.mock import AsyncMock, MagicMock
from adaptive_trust_medical_rag.llm_backend.live_provider_router import LiveProviderRouter
from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_routing.types import FailureClass
from adaptive_trust_medical_rag.llm_backend.interfaces import ProviderResponse

@pytest.fixture
def router():
    return LiveProviderRouter(provider_priority=["primary", "secondary"])

@pytest.fixture
def primary_adapter():
    mock = AsyncMock()
    mock.generate_structured = AsyncMock()
    return mock

@pytest.fixture
def secondary_adapter():
    mock = AsyncMock()
    mock.generate_structured = AsyncMock()
    return mock

@pytest.mark.asyncio
async def test_primary_provider_success(router, primary_adapter, secondary_adapter):
    router.register_provider("primary", primary_adapter)
    router.register_provider("secondary", secondary_adapter)
    
    expected = ProviderResponse(provider="primary", model="m1", request_id="1", content="test", structured_output={}, usage={}, latency_ms=10, finish_reason="stop", transport_status=200, raw_metadata={})
    primary_adapter.generate_structured.return_value = expected
    
    res = await router.generate_structured("prompt", {})
    assert res == expected
    primary_adapter.generate_structured.assert_called_once()
    secondary_adapter.generate_structured.assert_not_called()

@pytest.mark.asyncio
async def test_primary_provider_429_failover(router, primary_adapter, secondary_adapter):
    router.register_provider("primary", primary_adapter)
    router.register_provider("secondary", secondary_adapter)
    
    err = ModelExecutionError("429")
    err.failure_class = FailureClass.RATE_LIMIT
    primary_adapter.generate_structured.side_effect = err
    
    expected = ProviderResponse(provider="secondary", model="m2", request_id="2", content="test2", structured_output={}, usage={}, latency_ms=10, finish_reason="stop", transport_status=200, raw_metadata={})
    secondary_adapter.generate_structured.return_value = expected
    
    res = await router.generate_structured("prompt", {})
    assert res == expected
    primary_adapter.generate_structured.assert_called_once()
    secondary_adapter.generate_structured.assert_called_once()

@pytest.mark.asyncio
async def test_primary_provider_timeout_failover(router, primary_adapter, secondary_adapter):
    router.register_provider("primary", primary_adapter)
    router.register_provider("secondary", secondary_adapter)
    
    err = ModelExecutionError("timeout")
    err.failure_class = FailureClass.TIMEOUT
    primary_adapter.generate_structured.side_effect = err
    
    secondary_adapter.generate_structured.return_value = ProviderResponse(provider="secondary", model="m2", request_id="2", content="test2", structured_output={}, usage={}, latency_ms=10, finish_reason="stop", transport_status=200, raw_metadata={})
    await router.generate_structured("prompt", {})
    secondary_adapter.generate_structured.assert_called_once()

@pytest.mark.asyncio
async def test_all_providers_unavailable(router, primary_adapter, secondary_adapter):
    router.register_provider("primary", primary_adapter)
    router.register_provider("secondary", secondary_adapter)
    
    err1 = ModelExecutionError("429")
    err1.failure_class = FailureClass.RATE_LIMIT
    primary_adapter.generate_structured.side_effect = err1
    
    err2 = ModelExecutionError("503")
    err2.failure_class = FailureClass.TRANSIENT_PROVIDER
    secondary_adapter.generate_structured.side_effect = err2
    
    with pytest.raises(ModelExecutionError) as exc:
        await router.generate_structured("prompt", {})
    
    assert exc.value.failure_class == FailureClass.TRANSIENT_PROVIDER

@pytest.mark.asyncio
async def test_medical_failure_no_failover(router, primary_adapter, secondary_adapter):
    router.register_provider("primary", primary_adapter)
    router.register_provider("secondary", secondary_adapter)
    
    err = ModelExecutionError("Evidence insufficient")
    err.failure_class = FailureClass.UNKNOWN
    primary_adapter.generate_structured.side_effect = err
    
    with pytest.raises(ModelExecutionError) as exc:
        await router.generate_structured("prompt", {})
        
    assert "Evidence insufficient" in str(exc.value)
    secondary_adapter.generate_structured.assert_not_called()
