import os
from dataclasses import dataclass
from typing import Any, Protocol

from adaptive_trust_medical_rag.common.model_result import ModelGenerationResult


class ConfigurationError(RuntimeError):
    """Raised when the LLM backend is improperly configured."""
    pass


class LLMBackend(Protocol):
    def generate(self, prompt: str) -> Any: ...


@dataclass
class GenerationConfig:
    temperature: float = 0.0
    max_tokens: int | None = None


def get_backend() -> LLMBackend:
    from adaptive_trust_medical_rag.llm_routing.config import load_env_local
    load_env_local()

    mode = os.getenv("LLM_MODE")
    if mode == "DETERMINISTIC_MOCK":
        from .mock_backend import MockLLMBackend
        return MockLLMBackend()
    elif mode == "LIVE_LLM":
        from adaptive_trust_medical_rag.llm_routing.config import ProviderConfig, RoutingConfig
        from adaptive_trust_medical_rag.llm_routing.routed_llm_backend import RoutedLLMBackend
        from adaptive_trust_medical_rag.llm_routing.router import LLMProviderRouter
        from adaptive_trust_medical_rag.llm_routing.types import RoutingMode

        from .sync_adapter import SyncLLMBackendAdapter

        backends = {}
        providers_list = []
        gen_config = GenerationConfig()

        # Determine primary provider from env (default: groq for normal mode)
        primary = os.getenv("LLM_PRIMARY_PROVIDER", "groq")

        # Groq
        groq_api_key = (os.getenv("GROQ_API_KEY") or "").strip()
        if groq_api_key:
            from .groq_backend import GroqBackend
            groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
            backends["groq"] = GroqBackend(
                api_key=groq_api_key,
                model_name=groq_model,
                temperature=gen_config.temperature,
                max_tokens=gen_config.max_tokens,
            )
            groq_priority = 1 if primary == "groq" else 2
            providers_list.append(ProviderConfig(name="groq", priority=groq_priority, model_id=groq_model, api_key_env_var="GROQ_API_KEY"))

        # Gemini
        gemini_api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
        if gemini_api_key:
            from .google_gemini_backend import GoogleGeminiBackend
            gem_model = os.getenv("GEMINI_MODEL", "gemini-3.1-pro-preview")
            backends["gemini"] = GoogleGeminiBackend(api_key=gemini_api_key, model_name=gem_model)
            gemini_priority = 1 if primary == "gemini" else 2
            providers_list.append(ProviderConfig(name="gemini", priority=gemini_priority, model_id=gem_model, api_key_env_var="GEMINI_API_KEY"))

        # Cloudflare Workers AI (tertiary, optional)
        cf_token = (os.getenv("CLOUDFLARE_API_TOKEN") or "").strip()
        cf_account = (os.getenv("CLOUDFLARE_ACCOUNT_ID") or "").strip()
        if cf_token and cf_account:
            from .cloudflare_backend import CloudflareBackend
            cf_model = os.getenv("CLOUDFLARE_MODEL", "@cf/meta/llama-3.3-70b-instruct-fp8-fast")
            backends["cloudflare"] = CloudflareBackend(api_token=cf_token, account_id=cf_account, model_name=cf_model)
            providers_list.append(ProviderConfig(name="cloudflare", priority=3, model_id=cf_model, api_key_env_var="CLOUDFLARE_API_TOKEN"))

        # HuggingFace (quaternary, optional)
        hf_token = (os.getenv("HF_TOKEN") or "").strip()
        if hf_token:
            from .huggingface_backend import HuggingFaceBackend
            hf_model = os.getenv("HF_MODEL", "meta-llama/Llama-3.3-70B-Instruct")
            backends["huggingface"] = HuggingFaceBackend(token=hf_token, model_name=hf_model)
            providers_list.append(ProviderConfig(name="huggingface", priority=4, model_id=hf_model, api_key_env_var="HF_TOKEN"))

        if not backends:
            raise ConfigurationError("No valid provider configurations found for LIVE_LLM")

        routing_mode = RoutingMode.APPLICATION
        if os.getenv("SCIENTIFIC_MODE") == "1":
            routing_mode = RoutingMode.SCIENTIFIC

        config = RoutingConfig(mode=routing_mode, providers=providers_list)
        router = LLMProviderRouter(config=config, backends=backends)

        return SyncLLMBackendAdapter(RoutedLLMBackend(router=router))
    else:
        raise ConfigurationError(f"Invalid or missing LLM_MODE: {mode}")

