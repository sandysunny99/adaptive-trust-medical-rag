import pytest
from unittest.mock import AsyncMock, MagicMock
from adaptive_trust_medical_rag.llm_routing.config import RoutingConfig, ProviderConfig, RoutingMode
from adaptive_trust_medical_rag.llm_routing.router import LLMProviderRouter, ProviderAttemptResult
from adaptive_trust_medical_rag.llm_routing.types import FailureClass, AllProvidersUnavailableError, ExperimentProviderUnavailable
from adaptive_trust_medical_rag.common.model_result import ModelExecutionError

@pytest.fixture
def base_config():
    return RoutingConfig(
        providers=[
            ProviderConfig("gemini", 1, "gemini-3.1-pro-preview", "GEMINI_API_KEY"),
            ProviderConfig("groq", 2, "openai/gpt-oss-120b", "GROQ_API_KEY")
        ],
        mode=RoutingMode.APPLICATION,
        retry_max_attempts=0
    )

@pytest.mark.asyncio
async def test_1_gemini_success(base_config):
    mock_gemini = AsyncMock()
    mock_gemini.generate.return_value = MagicMock(response_text="Success", request_id="1", model="gemini-3.1-pro-preview")
    mock_groq = AsyncMock()
    
    router = LLMProviderRouter(base_config, {"gemini": mock_gemini, "groq": mock_groq})
    result = await router.generate("test")
    
    assert result.provider == "gemini"
    assert result.success is True
    mock_gemini.generate.assert_called_once()
    mock_groq.generate.assert_not_called()

@pytest.mark.asyncio
async def test_2_gemini_transient_fallback_normal(base_config):
    mock_gemini = AsyncMock()
    # Simulate transient error (503)
    error = Exception("503 Server Error")
    error.failure_class = FailureClass.TRANSIENT_PROVIDER
    mock_gemini.generate.side_effect = error
    
    mock_groq = AsyncMock()
    mock_groq.generate.return_value = MagicMock(response_text="Fallback success", model="openai/gpt-oss-120b")
    
    router = LLMProviderRouter(base_config, {"gemini": mock_gemini, "groq": mock_groq})
    result = await router.generate("test")
    
    assert result.provider == "groq"
    mock_gemini.generate.assert_called_once()
    mock_groq.generate.assert_called_once()

@pytest.mark.asyncio
async def test_3_gemini_auth_failure_no_transient(base_config):
    mock_gemini = AsyncMock()
    error = Exception("401 Unauthorized")
    error.failure_class = FailureClass.AUTHENTICATION
    mock_gemini.generate.side_effect = error
    
    mock_groq = AsyncMock()
    
    router = LLMProviderRouter(base_config, {"gemini": mock_gemini, "groq": mock_groq})
    
    with pytest.raises(ModelExecutionError, match="Non-transient error from gemini"):
        await router.generate("test")
        
    mock_groq.generate.assert_not_called()

@pytest.mark.asyncio
async def test_6_scientific_mode_no_fallback(base_config):
    base_config.mode = RoutingMode.SCIENTIFIC
    base_config.__post_init__()
    
    mock_gemini = AsyncMock()
    error = Exception("503 Server Error")
    error.failure_class = FailureClass.TRANSIENT_PROVIDER
    mock_gemini.generate.side_effect = error
    
    mock_groq = AsyncMock()
    
    router = LLMProviderRouter(base_config, {"gemini": mock_gemini, "groq": mock_groq})
    
    with pytest.raises(ExperimentProviderUnavailable):
        await router.generate("test")
        
    mock_groq.generate.assert_not_called()

@pytest.mark.asyncio
async def test_7_scientific_mode_provider_mismatch():
    config = RoutingConfig(
        providers=[ProviderConfig("gemini", 1, "gemini-3.1-pro-preview", "GEMINI_API_KEY")],
        mode=RoutingMode.SCIENTIFIC,
        retry_max_attempts=0
    )
    # If the provider is missing from backends entirely, it's a hard stop
    router = LLMProviderRouter(config, {"groq": AsyncMock()})
    
    with pytest.raises(ExperimentProviderUnavailable):
        await router.generate("test")

@pytest.mark.asyncio
async def test_10_both_credentials_missing(base_config):
    # If backends dict is empty because keys are missing, we expect an error
    router = LLMProviderRouter(base_config, {})
    with pytest.raises(AllProvidersUnavailableError):
        await router.generate("test")
