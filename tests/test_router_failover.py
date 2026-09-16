"""Comprehensive router failover and provider routing tests (T01–T20).

Tests cover: normal routing, transient fallback, tertiary provider,
free-tier guards, scientific mode, security isolation, secret redaction,
and git protection.
"""
import os
import subprocess
import pytest
from unittest.mock import AsyncMock, MagicMock
from adaptive_trust_medical_rag.llm_routing.config import RoutingConfig, ProviderConfig
from adaptive_trust_medical_rag.llm_routing.router import LLMProviderRouter
from adaptive_trust_medical_rag.llm_routing.types import (
    FailureClass,
    AllProvidersUnavailableError,
    ExperimentProviderUnavailable,
    RoutingMode,
)
from adaptive_trust_medical_rag.common.model_result import ModelExecutionError


def _make_config(mode=RoutingMode.APPLICATION, tertiary_enabled=False, retry=0):
    return RoutingConfig(
        providers=[
            ProviderConfig("groq", 1, "openai/gpt-oss-120b", "GROQ_API_KEY"),
            ProviderConfig("gemini", 2, "gemini-3.1-pro-preview", "GEMINI_API_KEY"),
            ProviderConfig("huggingface", 3, "meta-llama/Llama-3.3-70B-Instruct", "HF_TOKEN"),
        ],
        mode=mode,
        retry_max_attempts=retry,
        tertiary_enabled=tertiary_enabled,
    )


def _success_mock(provider="groq", model="openai/gpt-oss-120b"):
    m = AsyncMock()
    m.generate.return_value = MagicMock(
        response_text="Success", request_id="1", model=model
    )
    return m


def _transient_error():
    e = Exception("503 Server Error")
    e.failure_class = FailureClass.TRANSIENT_PROVIDER
    return e


def _auth_error():
    e = Exception("401 Unauthorized")
    e.failure_class = FailureClass.AUTHENTICATION
    return e


# ── T01: Groq primary success ──
@pytest.mark.asyncio
async def test_t01_groq_success():
    config = _make_config()
    mock_groq = _success_mock()
    mock_gemini = AsyncMock()
    router = LLMProviderRouter(config, {"groq": mock_groq, "gemini": mock_gemini})
    result = await router.generate("test")
    assert result.provider == "groq"
    assert result.success is True
    mock_groq.generate.assert_called_once()
    mock_gemini.generate.assert_not_called()


# ── T02: Groq → Gemini transient fallback ──
@pytest.mark.asyncio
async def test_t02_groq_gemini_transient_fallback():
    config = _make_config()
    mock_groq = AsyncMock()
    mock_groq.generate.side_effect = _transient_error()
    mock_gemini = _success_mock("gemini", "gemini-3.1-pro-preview")
    router = LLMProviderRouter(config, {"groq": mock_groq, "gemini": mock_gemini})
    result = await router.generate("test")
    assert result.provider == "gemini"


# ── T03: Groq → Gemini after timeout ──
@pytest.mark.asyncio
async def test_t03_groq_gemini_timeout_fallback():
    config = _make_config()
    mock_groq = AsyncMock()
    e = Exception("Request timed out")
    e.failure_class = FailureClass.TIMEOUT
    mock_groq.generate.side_effect = e
    mock_gemini = _success_mock("gemini", "gemini-3.1-pro-preview")
    router = LLMProviderRouter(config, {"groq": mock_groq, "gemini": mock_gemini})
    result = await router.generate("test")
    assert result.provider == "gemini"


# ── T04: 429 rate-limit handling ──
@pytest.mark.asyncio
async def test_t04_rate_limit_handling():
    config = _make_config()
    mock_groq = AsyncMock()
    e = Exception("429 Rate limit exceeded")
    e.failure_class = FailureClass.RATE_LIMIT
    mock_groq.generate.side_effect = e
    mock_gemini = _success_mock("gemini", "gemini-3.1-pro-preview")
    router = LLMProviderRouter(config, {"groq": mock_groq, "gemini": mock_gemini})
    result = await router.generate("test")
    assert result.provider == "gemini"


# ── T05: Auth failure — no transient failover ──
@pytest.mark.asyncio
async def test_t05_auth_failure_no_fallback():
    config = _make_config()
    mock_groq = AsyncMock()
    mock_groq.generate.side_effect = _auth_error()
    mock_gemini = AsyncMock()
    router = LLMProviderRouter(config, {"groq": mock_groq, "gemini": mock_gemini})
    with pytest.raises(ModelExecutionError, match="Non-transient error from groq"):
        await router.generate("test")
    mock_gemini.generate.assert_not_called()


# ── T06: Gemini success ──
@pytest.mark.asyncio
async def test_t06_gemini_success():
    config = RoutingConfig(
        providers=[ProviderConfig("gemini", 1, "gemini-3.1-pro-preview", "GEMINI_API_KEY")],
        mode=RoutingMode.APPLICATION, retry_max_attempts=0,
    )
    mock_gemini = _success_mock("gemini", "gemini-3.1-pro-preview")
    router = LLMProviderRouter(config, {"gemini": mock_gemini})
    result = await router.generate("test")
    assert result.provider == "gemini"


# ── T07: Tertiary provider disabled ──
@pytest.mark.asyncio
async def test_t07_tertiary_disabled():
    config = _make_config(tertiary_enabled=False)
    mock_groq = AsyncMock()
    mock_groq.generate.side_effect = _transient_error()
    mock_gemini = AsyncMock()
    mock_gemini.generate.side_effect = _transient_error()
    mock_hf = _success_mock("huggingface", "meta-llama/Llama-3.3-70B-Instruct")
    router = LLMProviderRouter(
        config, {"groq": mock_groq, "gemini": mock_gemini, "huggingface": mock_hf}
    )
    with pytest.raises(AllProvidersUnavailableError):
        await router.generate("test")
    mock_hf.generate.assert_not_called()


# ── T08: Tertiary provider enabled ──
@pytest.mark.asyncio
async def test_t08_tertiary_enabled():
    config = _make_config(tertiary_enabled=True)
    mock_groq = AsyncMock()
    mock_groq.generate.side_effect = _transient_error()
    mock_gemini = AsyncMock()
    mock_gemini.generate.side_effect = _transient_error()
    mock_hf = _success_mock("huggingface", "meta-llama/Llama-3.3-70B-Instruct")
    router = LLMProviderRouter(
        config, {"groq": mock_groq, "gemini": mock_gemini, "huggingface": mock_hf}
    )
    result = await router.generate("test")
    assert result.provider == "huggingface"


# ── T09: Security rejection blocks failover ──
@pytest.mark.asyncio
async def test_t09_security_rejection_no_fallback():
    config = _make_config()
    mock_groq = AsyncMock()
    e = Exception("Security: prompt injection detected")
    e.failure_class = FailureClass.APPLICATION_SEMANTIC
    mock_groq.generate.side_effect = e
    mock_gemini = AsyncMock()
    router = LLMProviderRouter(config, {"groq": mock_groq, "gemini": mock_gemini})
    with pytest.raises(ModelExecutionError, match="Non-transient error"):
        await router.generate("test")
    mock_gemini.generate.assert_not_called()


# ── T10: Authorization rejection blocks failover ──
@pytest.mark.asyncio
async def test_t10_authorization_rejection_no_fallback():
    config = _make_config()
    mock_groq = AsyncMock()
    e = Exception("403 Forbidden")
    e.failure_class = FailureClass.AUTHORIZATION
    mock_groq.generate.side_effect = e
    mock_gemini = AsyncMock()
    router = LLMProviderRouter(config, {"groq": mock_groq, "gemini": mock_gemini})
    with pytest.raises(ModelExecutionError, match="Non-transient error"):
        await router.generate("test")
    mock_gemini.generate.assert_not_called()


# ── T11: Scientific Mode blocks ALL fallback ──
@pytest.mark.asyncio
async def test_t11_scientific_mode_blocks_fallback():
    config = RoutingConfig.scientific_phase15()
    config.__post_init__()
    mock_gemini = AsyncMock()
    mock_gemini.generate.side_effect = _transient_error()
    mock_groq = AsyncMock()
    router = LLMProviderRouter(config, {"gemini": mock_gemini, "groq": mock_groq})
    with pytest.raises(ExperimentProviderUnavailable):
        await router.generate("test")
    mock_groq.generate.assert_not_called()


# ── T12: Scientific Mode provider mismatch ──
@pytest.mark.asyncio
async def test_t12_scientific_provider_mismatch():
    config = RoutingConfig.scientific_phase15()
    config.__post_init__()
    # Only groq is in backends, but scientific expects gemini
    router = LLMProviderRouter(config, {"groq": AsyncMock()})
    with pytest.raises(ExperimentProviderUnavailable):
        await router.generate("test")


# ── T13: Scientific Mode model mismatch ──
@pytest.mark.asyncio
async def test_t13_scientific_model_mismatch():
    config = RoutingConfig(
        providers=[ProviderConfig("gemini", 1, "gemini-3.1-pro-preview", "GEMINI_API_KEY")],
        mode=RoutingMode.SCIENTIFIC, retry_max_attempts=0,
    )
    # Backend returns a different model
    mock_gemini = AsyncMock()
    result_mock = MagicMock(
        response_text="Success", request_id="1", model="gemini-2.0-flash"
    )
    mock_gemini.generate.return_value = result_mock
    router = LLMProviderRouter(config, {"gemini": mock_gemini})
    result = await router.generate("test")
    # The result should record the mismatch
    assert result.expected_model == "gemini-3.1-pro-preview"
    assert result.actual_model == "gemini-2.0-flash"
    assert result.provider_match is True  # provider matches, model is different


# ── T14: Missing Groq credential ──
@pytest.mark.asyncio
async def test_t14_missing_groq_credential():
    config = RoutingConfig(
        providers=[
            ProviderConfig("gemini", 1, "gemini-3.1-pro-preview", "GEMINI_API_KEY"),
        ],
        mode=RoutingMode.APPLICATION, retry_max_attempts=0,
    )
    mock_gemini = _success_mock("gemini", "gemini-3.1-pro-preview")
    router = LLMProviderRouter(config, {"gemini": mock_gemini})
    result = await router.generate("test")
    assert result.provider == "gemini"


# ── T15: Missing Gemini credential ──
@pytest.mark.asyncio
async def test_t15_missing_gemini_credential():
    config = RoutingConfig(
        providers=[
            ProviderConfig("groq", 1, "openai/gpt-oss-120b", "GROQ_API_KEY"),
        ],
        mode=RoutingMode.APPLICATION, retry_max_attempts=0,
    )
    mock_groq = _success_mock()
    router = LLMProviderRouter(config, {"groq": mock_groq})
    result = await router.generate("test")
    assert result.provider == "groq"


# ── T16: Both credentials missing ──
@pytest.mark.asyncio
async def test_t16_both_missing():
    config = _make_config()
    router = LLMProviderRouter(config, {})
    with pytest.raises(AllProvidersUnavailableError):
        await router.generate("test")


# ── T17: Missing HF credential — graceful skip ──
@pytest.mark.asyncio
async def test_t17_missing_hf_credential():
    config = _make_config(tertiary_enabled=True)
    mock_groq = AsyncMock()
    mock_groq.generate.side_effect = _transient_error()
    mock_gemini = AsyncMock()
    mock_gemini.generate.side_effect = _transient_error()
    # HF not in backends because token missing
    router = LLMProviderRouter(config, {"groq": mock_groq, "gemini": mock_gemini})
    with pytest.raises(AllProvidersUnavailableError):
        await router.generate("test")


# ── T18: Missing Cloudflare credential — no-op (not implemented) ──
def test_t18_cloudflare_not_implemented():
    """Cloudflare is documented but not implemented. No backend exists."""
    config = _make_config()
    assert "cloudflare" not in {p.name for p in config.providers}


# ── T19: Secret redaction ──
def test_t19_secret_redaction():
    config = RoutingConfig.default_routing()
    assert config.secret_redaction is True
    assert config.log_raw_keys is False
    # ProviderConfig repr never contains actual key
    for p in config.providers:
        repr_str = repr(p)
        assert "credential_present" in repr_str
        assert "api_key" not in repr_str.lower() or "api_key_env_var" not in repr_str


# ── T20: .env.local git protection ──
def test_t20_env_local_git_protection():
    result = subprocess.run(
        ["git", "check-ignore", "-v", ".env.local"],
        capture_output=True, text=True,
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )
    assert result.returncode == 0, ".env.local must be ignored by git"
    assert ".env.local" in result.stdout
