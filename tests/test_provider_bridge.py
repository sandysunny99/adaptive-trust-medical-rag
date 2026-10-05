import asyncio

import pytest

from adaptive_trust_medical_rag.common.model_result import (
    ModelExecutionError,
    ModelGenerationResult,
)
from adaptive_trust_medical_rag.llm_backend import get_backend
from adaptive_trust_medical_rag.llm_backend.sync_adapter import SyncLLMBackendAdapter
from adaptive_trust_medical_rag.llm_routing.routed_llm_backend import RoutedLLMBackend


class DummyAsyncBackend:
    async def generate(self, prompt: str) -> ModelGenerationResult:
        return ModelGenerationResult(
            provider="dummy",
            model="dummy-model",
            local_execution_id="123",
            request_id=None,
            response_id=None,
            request_started_at="2024-01-01T00:00:00Z",
            response_received_at="2024-01-01T00:00:01Z",
            finish_reason="stop",
            response_text=f"Response for: {prompt}",
            response_hash="abc",
            response_length=10,
            response_preview="Response",
            input_tokens=10,
            output_tokens=10,
            provider_call_latency_ms=100.0,
            network_latency_ms=None,
            generation_latency_ms=None,
            total_generation_latency_ms=None,
            status="SUCCESS",
        )

class ExceptionAsyncBackend:
    async def generate(self, prompt: str) -> ModelGenerationResult:
        raise ModelExecutionError("API Error", status_code="500")

class TimeoutAsyncBackend:
    async def generate(self, prompt: str) -> ModelGenerationResult:
        raise ModelExecutionError("Timeout", status_code="TIMEOUT")

class EmptyAsyncBackend:
    async def generate(self, prompt: str) -> ModelGenerationResult:
        return ModelGenerationResult(
            provider="dummy",
            model="dummy",
            local_execution_id="123",
            request_id=None,
            response_id=None,
            request_started_at="",
            response_received_at="",
            finish_reason="",
            response_text="",
            response_hash="",
            response_length=0,
            response_preview="",
            input_tokens=0,
            output_tokens=0,
            provider_call_latency_ms=0.0,
            network_latency_ms=None,
            generation_latency_ms=None,
            total_generation_latency_ms=None,
            status="EMPTY_RESPONSE",
        )

def test_gc01_sync_adapter_returns_str():
    adapter = SyncLLMBackendAdapter(DummyAsyncBackend())
    result = adapter.generate("test prompt")
    assert isinstance(result, str)
    assert result == "Response for: test prompt"

def test_gc02_correct_model_result_extracted():
    adapter = SyncLLMBackendAdapter(DummyAsyncBackend())
    adapter.generate("test prompt")
    assert adapter.last_result is not None
    assert adapter.last_result.response_text == "Response for: test prompt"

def test_gc03_provider_exception_propagates():
    adapter = SyncLLMBackendAdapter(ExceptionAsyncBackend())
    with pytest.raises(ModelExecutionError) as exc:
        adapter.generate("test prompt")
    assert "API Error" in str(exc.value)
    assert exc.value.status_code == "500"

def test_gc04_timeout_propagates():
    adapter = SyncLLMBackendAdapter(TimeoutAsyncBackend())
    with pytest.raises(ModelExecutionError) as exc:
        adapter.generate("test prompt")
    assert "Timeout" in str(exc.value)
    assert exc.value.status_code == "TIMEOUT"

def test_gc05_empty_result_handled_safely():
    adapter = SyncLLMBackendAdapter(EmptyAsyncBackend())
    result = adapter.generate("test prompt")
    assert result == ""

@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    monkeypatch.delenv("LLM_MODE", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

def test_gc06_adapter_does_not_break_mock_backend(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "DETERMINISTIC_MOCK")
    backend = get_backend()
    # MockLLMBackend is untouched and remains async
    import inspect
    assert inspect.iscoroutinefunction(backend.generate)

def test_gc07_gc08_provider_factory_returns_orchestrator_compatible_backend(monkeypatch):
    monkeypatch.setenv("LLM_MODE", "LIVE_LLM")
    monkeypatch.setenv("GROQ_API_KEY", "dummy_key")
    backend = get_backend()

    assert isinstance(backend, SyncLLMBackendAdapter)
    assert isinstance(backend.async_backend, RoutedLLMBackend)
    import inspect
    assert not inspect.iscoroutinefunction(backend.generate)

def test_gc09_gc10_groq_request_parameters():
    from adaptive_trust_medical_rag.llm_backend.groq_backend import GroqBackend
    groq = GroqBackend(api_key="key", temperature=0.0)
    assert groq.temperature == 0.0
    assert not hasattr(groq, "seed") # Seed is unsupported in the current config

def test_event_loop_safety():
    # Calling the sync adapter inside an already running event loop should not crash
    # (avoid asyncio.run() conflict)
    adapter = SyncLLMBackendAdapter(DummyAsyncBackend())

    async def run_in_loop():
        return adapter.generate("test prompt in loop")

    loop = asyncio.new_event_loop()
    result = loop.run_until_complete(run_in_loop())
    loop.close()

    assert result == "Response for: test prompt in loop"

