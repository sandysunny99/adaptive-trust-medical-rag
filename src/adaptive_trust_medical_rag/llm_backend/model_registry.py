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
    required_env_vars: tuple[str, ...] = ()
    is_test_only: bool = False


# Canonical registry of supported answer-generation models
SUPPORTED_LLM_MODELS: list[LLMModelDefinition] = [
    LLMModelDefinition(
        id="nvidia/nemotron-3-super-120b-a12b",
        provider="nvidia",
        name="NVIDIA Nemotron-3 Super 120B",
        description="High-capacity biomedical-reasoning LLM hosted on NVIDIA NIM.",
        env_key="NVIDIA_API_KEY",
        required_env_vars=("NVIDIA_API_KEY",),
    ),
    LLMModelDefinition(
        id="openai/gpt-oss-120b",
        provider="groq",
        name="Groq GPT-OSS 120B",
        description="Open-weights model inference hosted on Groq.",
        env_key="GROQ_API_KEY",
        required_env_vars=("GROQ_API_KEY",),
    ),
    LLMModelDefinition(
        id="@cf/meta/llama-3.3-70b-instruct-fp8-fast",
        provider="cloudflare",
        name="Cloudflare Llama-3.3 70B Instruct",
        description="Serverless Workers AI instance with edge compliance.",
        env_key="CLOUDFLARE_API_TOKEN",
        required_env_vars=("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"),
    ),
    LLMModelDefinition(
        id="mock-llm",
        provider="mock",
        name="Deterministic Mock LLM (Testing)",
        description="Deterministic testbed model for CI and offline evaluation.",
        env_key=None,
        is_test_only=True,
    ),
]


def get_model_definition(model_id: str) -> LLMModelDefinition | None:
    """Look up a model definition by its canonical ID."""
    for m in SUPPORTED_LLM_MODELS:
        if m.id == model_id:
            return m
    return None


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
        # Check credentials requirement
        req_vars = m.required_env_vars if m.required_env_vars else ((m.env_key,) if m.env_key else ())
        has_credentials = all(bool(os.getenv(k)) for k in req_vars) if req_vars else True

        if is_testing:
            is_available = True
        elif m.provider in registered_providers:
            is_available = True
        elif has_credentials and not m.is_test_only:
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


def validate_llm_selection(
    selection: Any,
    app_state: Any = None,
) -> tuple[bool, str | None, LLMModelDefinition | None]:
    """Strict server-side validation of user LLM model selection.

    Rules:
    - If selection is None or mode is 'auto', valid (returns True, None, None).
    - If mode is 'manual':
      - Must provide a non-empty model_id.
      - model_id must exist in SUPPORTED_LLM_MODELS registry.
      - If provider is explicitly specified, it MUST match model_def.provider (no client overrides).
      - Model must be available/configured in app_state.llm_backend or environment (or testing mode).

    Returns:
        (is_valid, error_message_if_invalid, model_definition_if_manual)
    """
    if selection is None:
        return True, None, None

    if hasattr(selection, "model_dump"):
        data = selection.model_dump()
    elif isinstance(selection, dict):
        data = selection
    else:
        return False, "Invalid llm_selection data type", None

    mode = data.get("mode", "auto")
    if mode == "auto":
        return True, None, None

    if mode != "manual":
        return False, f"Unsupported selection mode: '{mode}'. Must be 'auto' or 'manual'.", None

    model_id = data.get("model_id")
    if not model_id:
        return False, "Manual mode requires a valid 'model_id'.", None

    model_def = get_model_definition(model_id)
    if model_def is None:
        return False, f"Unsupported or unknown model ID: '{model_id}'", None

    # Verify provider consistency
    client_provider = data.get("provider")
    if client_provider and client_provider.strip().lower() != model_def.provider.lower():
        return False, (
            f"Provider mismatch for model '{model_id}': "
            f"expected '{model_def.provider}', got '{client_provider}'"
        ), None

    # Verify availability/configuration
    is_testing = os.getenv("TESTING") == "1"
    router = getattr(app_state, "llm_backend", None) if app_state else None
    registered_providers: set[str] = set()
    if router and hasattr(router, "providers"):
        registered_providers = set(router.providers.keys())

    req_vars = model_def.required_env_vars if model_def.required_env_vars else ((model_def.env_key,) if model_def.env_key else ())
    has_credentials = all(bool(os.getenv(k)) for k in req_vars) if req_vars else True

    is_available = (
        is_testing
        or model_def.provider in registered_providers
        or (has_credentials and not model_def.is_test_only)
    )

    if not is_available:
        return False, (
            f"Model '{model_id}' ({model_def.name}) is not configured or available on the server."
        ), None

    return True, None, model_def
