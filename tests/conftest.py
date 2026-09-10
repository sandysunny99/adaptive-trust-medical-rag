import os

import pytest


@pytest.fixture(autouse=True)
def _set_default_llm_mode(monkeypatch):
    if not os.environ.get("LLM_MODE"):
        monkeypatch.setenv("LLM_MODE", "DETERMINISTIC_MOCK")
