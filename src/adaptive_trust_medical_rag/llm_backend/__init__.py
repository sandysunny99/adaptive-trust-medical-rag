import os
from typing import Protocol

from adaptive_trust_medical_rag.common.model_result import ModelGenerationResult


class ConfigurationError(RuntimeError):
    """Raised when the LLM backend is improperly configured."""
    pass


class LLMBackend(Protocol):
    async def generate(self, prompt: str) -> ModelGenerationResult: ...


def get_backend() -> LLMBackend:
    mode = os.getenv("LLM_MODE")
    if mode == "DETERMINISTIC_MOCK":
        from .mock_backend import MockLLMBackend
        return MockLLMBackend()
    elif mode == "LIVE_LLM":
        provider = os.getenv("LLM_PROVIDER")
        if provider == "gemini":
            model = os.getenv("LLM_MODEL")
            if not model:
                raise ConfigurationError("LLM_MODEL must be set for LIVE_LLM mode")
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ConfigurationError("GEMINI_API_KEY must be set for LIVE_LLM mode")
            from .google_gemini_backend import GoogleGeminiBackend
            return GoogleGeminiBackend(api_key=api_key, model_name=model)
        elif provider == "groq":
            model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ConfigurationError("GROQ_API_KEY must be set for groq provider")
            from .groq_backend import GroqBackend
            return GroqBackend(api_key=api_key, model_name=model)
        else:
            raise ConfigurationError(f"Unsupported provider: {provider}")
    else:
        raise ConfigurationError(f"Invalid or missing LLM_MODE: {mode}")
