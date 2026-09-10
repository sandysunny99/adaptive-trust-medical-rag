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
        from adaptive_trust_medical_rag.llm_routing.router import LLMProviderRouter
        from adaptive_trust_medical_rag.llm_routing.config import RoutingConfig, ProviderConfig
        from adaptive_trust_medical_rag.llm_routing.routed_llm_backend import RoutedLLMBackend
        from adaptive_trust_medical_rag.llm_routing.types import RoutingMode
        
        backends = {}
        providers_list = []
        
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            from .google_gemini_backend import GoogleGeminiBackend
            gem_model = os.getenv("LLM_MODEL", "gemini-2.5-pro")
            backends["gemini"] = GoogleGeminiBackend(api_key=gemini_api_key, model_name=gem_model)
            providers_list.append(ProviderConfig(name="gemini", priority=1, model_id=gem_model, api_key_env_var="GEMINI_API_KEY"))
            
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            from .groq_backend import GroqBackend
            groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
            backends["groq"] = GroqBackend(api_key=groq_api_key, model_name=groq_model)
            providers_list.append(ProviderConfig(name="groq", priority=2, model_id=groq_model, api_key_env_var="GROQ_API_KEY"))

        if not backends:
            raise ConfigurationError("No valid provider configurations found for LIVE_LLM")
            
        primary = os.getenv("LLM_PROVIDER", "gemini")
        for p in providers_list:
            if p.name == primary:
                p.priority = 0  # ensure it's first
            
        routing_mode = RoutingMode.APPLICATION
        if os.getenv("SCIENTIFIC_MODE") == "1":
            routing_mode = RoutingMode.SCIENTIFIC
            
        config = RoutingConfig(mode=routing_mode, providers=providers_list)
        router = LLMProviderRouter(config=config, backends=backends)
        
        return RoutedLLMBackend(router=router)
    else:
        raise ConfigurationError(f"Invalid or missing LLM_MODE: {mode}")
