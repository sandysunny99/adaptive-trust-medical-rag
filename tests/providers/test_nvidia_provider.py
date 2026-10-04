import pytest
import httpx
from unittest.mock import patch, AsyncMock
from adaptive_trust_medical_rag.llm_backend.openai_compatible_backend import OpenAICompatibleBackend
from adaptive_trust_medical_rag.llm_backend.live_provider_router import LiveProviderRouter
from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_routing.types import FailureClass

@pytest.fixture
def nvidia_backend():
    return OpenAICompatibleBackend(
        provider_name="nvidia",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key="FAKE_TEST_KEY_THAT_WILL_NOT_TRIGGER_GITLEAKS_12345",
        model_name="nvidia/nemotron-3-super-120b-a12b"
    )

@pytest.mark.asyncio
async def test_nvidia_connectivity(nvidia_backend):
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        res = await nvidia_backend.health_check()
        assert res is True

@pytest.mark.asyncio
async def test_nvidia_missing_key():
    backend = OpenAICompatibleBackend("nvidia", "url", "", "model")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 401
        mock_post.return_value.text = "Unauthorized"
        try:
            await backend.generate("hello")
            assert False, "Should raise auth error"
        except ModelExecutionError as e:
            assert getattr(e, "failure_class", None) == FailureClass.AUTHENTICATION

@pytest.mark.asyncio
async def test_nvidia_structured_parsing(nvidia_backend):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        class MockResp:
            status_code = 200
            def json(self):
                return {
                    "id": "req-123",
                    "choices": [{"message": {"content": '{"test": "ok"}'}, "finish_reason": "stop"}]
                }
        mock_post.return_value = MockResp()
        res = await nvidia_backend.generate_structured("hello", {"type": "json_object"})
        assert res.structured_output == {"test": "ok"}
        assert res.provider == "nvidia"

@pytest.mark.asyncio
async def test_live_router_fallback():
    router = LiveProviderRouter(primary_provider="nvidia", secondary_provider="groq")
    
    mock_nvidia = AsyncMock()
    # Simulate a network/timeout error that should trigger fallback
    err = ModelExecutionError("Timeout", status_code="TIMEOUT")
    err.failure_class = FailureClass.TIMEOUT
    mock_nvidia.generate_structured.side_effect = err
    
    mock_groq = AsyncMock()
    class DummyRes:
        pass
    mock_groq.generate_structured.return_value = DummyRes()
    
    router.register_provider("nvidia", mock_nvidia)
    router.register_provider("groq", mock_groq)
    
    res = await router.generate_structured("test", {})
    assert isinstance(res, DummyRes)
    
    # Simulate a non-fallback error (semantic/content)
    err_semantic = ModelExecutionError("Schema error", status_code="400")
    err_semantic.failure_class = FailureClass.INVALID_REQUEST
    mock_nvidia.generate_structured.side_effect = err_semantic
    
    try:
        await router.generate_structured("test", {})
        assert False, "Should not fallback for INVALID_REQUEST"
    except ModelExecutionError as e:
        assert getattr(e, "failure_class", None) == FailureClass.INVALID_REQUEST
