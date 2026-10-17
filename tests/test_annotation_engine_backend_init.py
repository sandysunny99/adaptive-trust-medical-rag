"""AIAnnotationEngine backend initialization for the fallback providers (Bandit B110, option a).

A failed HuggingFace/FreeLLMAPI adapter initialization is now logged with the provider and the
exception type only (never the message, which can carry a key or a URL) and still leaves no
backend, so annotate_position fails safely with the "not configured or missing credentials" error.
Prompts and schema are synthetic files in a temporary directory; the adapter is replaced.
"""

from __future__ import annotations

import asyncio
import json
import logging
from types import SimpleNamespace

import pytest

from adaptive_trust_medical_rag.annotation import engine as engine_module
from adaptive_trust_medical_rag.annotation.engine import AIAnnotationEngine
from adaptive_trust_medical_rag.annotation.schemas import AnnotationSessionConfig
from adaptive_trust_medical_rag.llm_backend import pilot_adapter

SECRET_LIKE = "token=example-not-a-real-credential https://internal.example.invalid/v1"


@pytest.fixture
def workspace(tmp_path):
    for name in ("system.txt", "adjudication.txt", "challenge.txt"):
        (tmp_path / name).write_text("Query: {query}\nEvidence: {evidence}\n", encoding="utf-8")
    (tmp_path / "schema.json").write_text(json.dumps({"type": "object"}), encoding="utf-8")
    return tmp_path


def make_engine(workspace, provider: str) -> AIAnnotationEngine:
    config = AnnotationSessionConfig(
        provider=provider, model="test-model", verify_prompt_hashes=False,
        system_prompt_path="system.txt", adjudication_prompt_path="adjudication.txt",
        challenge_prompt_path="challenge.txt", schema_path="schema.json",
    )
    return AIAnnotationEngine(config, workspace_dir=workspace)


class FakeAdapter:
    def __init__(self, execution_mode, model, structured_output_method="JSON_OBJECT"):
        self.execution_mode, self.model = execution_mode, model


class FailingAdapter:
    def __init__(self, *args, **kwargs):
        raise RuntimeError(f"could not reach the gateway ({SECRET_LIKE})")


@pytest.mark.parametrize(("provider", "mode"), [("huggingface", "DIRECT_HUGGINGFACE"),
                                                 ("freellmapi", "FREELLMAPI_GATEWAY")])
def test_a_fallback_provider_initializes_its_adapter(workspace, monkeypatch, provider, mode):
    monkeypatch.setattr(pilot_adapter, "LLMProviderAdapter", FakeAdapter)
    backend = make_engine(workspace, provider).llm_backend
    assert isinstance(backend, FakeAdapter) and backend.execution_mode == mode


def test_a_failed_adapter_initialization_is_logged_without_its_message(workspace, monkeypatch, caplog):
    monkeypatch.setattr(pilot_adapter, "LLMProviderAdapter", FailingAdapter)
    with caplog.at_level(logging.WARNING, logger=engine_module.__name__):
        engine = make_engine(workspace, "huggingface")
    assert engine.llm_backend is None
    (record,) = [r for r in caplog.records if "adapter initialization failed" in r.getMessage()]
    assert record.levelno == logging.WARNING
    assert "huggingface" in record.getMessage() and "RuntimeError" in record.getMessage()
    assert SECRET_LIKE not in caplog.text and "gateway" not in caplog.text


def test_without_a_backend_annotation_still_fails_safely(workspace, monkeypatch):
    monkeypatch.setattr(pilot_adapter, "LLMProviderAdapter", FailingAdapter)
    engine = make_engine(workspace, "huggingface")
    position = SimpleNamespace(query_text="synthetic query", retrieved_evidence="synthetic evidence")
    with pytest.raises(RuntimeError, match="not configured or missing credentials"):
        asyncio.run(engine.annotate_position(position))


def test_an_unknown_provider_still_has_no_backend_and_logs_nothing(workspace, caplog):
    with caplog.at_level(logging.WARNING, logger=engine_module.__name__):
        engine = make_engine(workspace, "no-such-provider")
    assert engine.llm_backend is None
    assert "adapter initialization failed" not in caplog.text
