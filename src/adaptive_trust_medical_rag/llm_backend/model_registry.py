"""Model registry and catalog for user-selectable LLM answer generation.

Defines supported models, their metadata, and providers.
Enforces strict segregation:
- Selected LLM: used ONLY for final analysis generation.
- PubMedBERT-MNLI-MedNLI: used ONLY for claim verification.
- all-MiniLM-L6-v2: used ONLY for dense retrieval embeddings.
- Vision model: used ONLY for prescription OCR extraction.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LLMModelDefinition:
    id: str
    provider: str
    name: str
    description: str
    env_key: str | None = None


# Canonical registry of supported answer-generation models
SUPPORTED_LLM_MODELS: list[LLMModelDefinition] = [
    LLMModelDefinition(
        id="nvidia/nemotron-3-super-120b-a12b",
        provider="nvidia",
        name="NVIDIA Nemotron-3 Super 120B",
        description="High-capacity biomedical-reasoning LLM hosted on NVIDIA NIM.",
        env_key="NVIDIA_API_KEY",
    ),
    LLMModelDefinition(
        id="openai/gpt-oss-120b",
        provider="groq",
        name="Groq Llama-3.3 70B Versatile",
        description="Ultra-low latency inference engine for rapid pharmacology synthesis.",
        env_key="GROQ_API_KEY",
    ),
    LLMModelDefinition(
        id="@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        provider="cloudflare",
        name="Cloudflare Llama-3.3 70B Instruct",
        description="Serverless Workers AI instance with edge compliance.",
        env_key="CLOUDFLARE_API_TOKEN",
    ),
    LLMModelDefinition(
        id="mock-llm",
        provider="mock",
        name="Deterministic Mock LLM (Testing)",
        description="Deterministic testbed model for CI and offline evaluation.",
        env_key=None,
    ),
]


def get_available_models(app_state: Any = None) -> list[dict[str, Any]]:
    """Return the list of supported models with their current availability status.

    A model is available if its provider is registered in app_state.llm_backend,
    or if its required API credentials are present in the environment (or in testing mode).
    """
    is_testing = os.getenv("TESTING") == "1"
    router = getattr(app_state, "llm_backend", None) if app_state else None
    registered_providers: set[str] = set()

    if router and hasattr(router, "providers"):
        registered_providers = set(router.providers.keys())

    models = []
    for m in SUPPORTED_LLM_MODELS:
        # Check availability
        if is_testing:
            is_available = True
        elif m.provider in registered_providers:
            is_available = True
        elif m.env_key and os.getenv(m.env_key):
            is_available = True
        else:
            is_available = False

        models.append({
            "id": m.id,
            "provider": m.provider,
            "name": m.name,
            "description": m.description,
            "is_available": is_available,
        })

    return models
