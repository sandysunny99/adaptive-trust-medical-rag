import inspect
import uuid
from datetime import datetime, timezone
from hashlib import sha256

import pytest

from adaptive_trust_medical_rag.common.model_result import ModelGenerationResult
from adaptive_trust_medical_rag.llm_backend import ConfigurationError, get_backend


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("LLM_MODE", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def test_factory_returns_mock_backend(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "DETERMINISTIC_MOCK")
    backend = get_backend()
    assert hasattr(backend, "generate")
    assert inspect.iscoroutinefunction(backend.generate)


@pytest.mark.asyncio
async def test_mock_backend_generates_expected_result(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "DETERMINISTIC_MOCK")
    backend = get_backend()

    prompt = "What is the mechanism of action of aspirin?"
    result: ModelGenerationResult = await backend.generate(prompt)

    assert isinstance(result, ModelGenerationResult)
    assert result.provider == "mock"
    assert result.model == "deterministic-mock"

    assert result.input_tokens is None
    assert result.output_tokens is None
    assert result.status == "SUCCESS"

    uuid_obj = uuid.UUID(result.local_execution_id)
    assert str(uuid_obj) == result.local_execution_id

    assert result.request_id is None
    assert result.response_id is None
    assert result.finish_reason is None

    # Validate timestamps and their order
    for ts in (result.request_started_at, result.response_received_at):
        dt = datetime.fromisoformat(ts)
        assert dt.tzinfo == timezone.utc
    assert result.request_started_at <= result.response_received_at

    expected_text = f"Evidence-grounded response for query context: {prompt[:150]}..."
    assert result.response_text == expected_text

    expected_hash = sha256(expected_text.encode("utf-8")).hexdigest()
    assert result.response_hash == expected_hash

    assert result.provider_call_latency_ms == 0.0
    assert result.network_latency_ms is None
    assert result.generation_latency_ms is None
    assert result.total_generation_latency_ms is None


def test_factory_raises_on_invalid_config(monkeypatch):
    with pytest.raises(ConfigurationError):
        get_backend()

    monkeypatch.setenv("LLM_MODE", "UNKNOWN")
    with pytest.raises(ConfigurationError):
        get_backend()

    # Ensure no credentials leak from .env.local for the no-credential test
    # Use empty strings (not delenv) so load_env_local() won't re-populate them
    monkeypatch.setenv("LLM_MODE", "LIVE_LLM")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("HF_TOKEN", "")
    monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "")
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "")
    with pytest.raises(ConfigurationError):
        get_backend()
    monkeypatch.setenv("GEMINI_API_KEY", "dummy")
    backend = get_backend()
    assert hasattr(backend, "generate")

