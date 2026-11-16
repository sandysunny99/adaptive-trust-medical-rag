"""The provider decision of 2026-10-24: Groq first, Cloudflare as the only fallback, NVIDIA held back.

The live configuration sets LLM_PROVIDER=groq and LLM_FALLBACK_PROVIDERS=cloudflare while an
NVIDIA key is also present (its chat model answered HTTP 404). These tests build the router with
build_llm_router() from that configuration, then swap each registered backend for a fake, so no
real provider is called and the order under test is the one the application builds.
"""

from __future__ import annotations

import asyncio
import time

import pytest

from adaptive_trust_medical_rag.api import app as app_module
from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_backend.interfaces import ProviderResponse
from adaptive_trust_medical_rag.llm_routing.types import FailureClass

FAKE_KEY = "FAKE_TEST_KEY_NOT_A_SECRET_0000"
ENV = (
    "LLM_PROVIDER",
    "LLM_PRIMARY_PROVIDER",
    "LLM_FALLBACK_PROVIDERS",
    "LLM_FALLBACK_PROVIDER",
    "LLM_FAILOVER_ENABLED",
    "LLM_REQUEST_DEADLINE_S",
    "GROQ_API_KEY",
    "GROQ_MODEL",
    "NVIDIA_LLM_API_KEY",
    "NVIDIA_API_KEY",
    "NVIDIA_LLM_MODEL",
    "CLOUDFLARE_API_TOKEN",
    "CLOUDFLARE_ACCOUNT_ID",
    "CLOUDFLARE_MODEL",
    "CLOUDFLARE_ENABLED",
)


class Fake:
    def __init__(self, name: str, *errors: Exception, delay: float = 0.0):
        self.name, self.errors, self.delay, self.calls = name, list(errors), delay, 0

    def get_model_metadata(self):
        return {"provider": self.name, "model": f"{self.name}-model"}

    async def generate_structured(self, prompt, response_format):
        self.calls += 1
        if self.delay:
            await asyncio.sleep(self.delay)
        if self.errors:
            raise self.errors.pop(0)
        return ProviderResponse(
            provider=self.name,
            model=f"{self.name}-model",
            request_id="r",
            content="{}",
            structured_output={},
            usage={},
            latency_ms=1.0,
            finish_reason="stop",
            transport_status=200,
            raw_metadata={},
        )


def failure(fc: FailureClass, status: str) -> ModelExecutionError:
    err = ModelExecutionError(f"simulated {fc.value}", status_code=status)
    err.failure_class = fc
    return err


@pytest.fixture
def decided(monkeypatch):
    """The router build_llm_router() makes from the decided configuration, with fake backends."""
    for k in ENV:
        monkeypatch.delenv(k, raising=False)
    for k in ("GROQ_API_KEY", "NVIDIA_API_KEY", "CLOUDFLARE_API_TOKEN"):
        monkeypatch.setenv(k, FAKE_KEY)
    monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "acct")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDERS", "cloudflare")
    monkeypatch.setenv(
        "CLOUDFLARE_ENABLED", "false"
    )  # as in the live files; not read by the router

    def build(groq=(), cloudflare=(), nvidia=(), groq_delay=0.0, deadline=None):
        if deadline is not None:
            monkeypatch.setenv("LLM_REQUEST_DEADLINE_S", str(deadline))
        router, config = app_module.build_llm_router()
        fakes = {
            "groq": Fake("groq", *groq, delay=groq_delay),
            "cloudflare": Fake("cloudflare", *cloudflare),
            "nvidia": Fake("nvidia", *nvidia),
        }
        assert set(router.providers) == set(fakes)  # all three are registered ...
        for name, fake in fakes.items():
            router.register_provider(name, fake)
        return router, config, fakes

    return build


def run(router, **kwargs):
    return asyncio.run(router.generate_structured("prompt", {"type": "json_object"}, **kwargs))


def test_the_order_is_groq_then_cloudflare_and_nvidia_is_left_out(decided):
    _, config, _ = decided()
    # ... but only Groq and Cloudflare are in the automatic order, with the decided models.
    assert config["order"] == [
        {"provider": "groq", "model": "openai/gpt-oss-120b"},
        {"provider": "cloudflare", "model": "@cf/meta/llama-3.3-70b-instruct-fp8-fast"},
    ]
    assert config["failover_enabled"] is True
    assert FAKE_KEY not in repr(config)


def test_a_groq_answer_never_calls_cloudflare_or_nvidia(decided):
    router, _, fakes = decided()
    assert run(router).provider == "groq"
    assert (fakes["groq"].calls, fakes["cloudflare"].calls, fakes["nvidia"].calls) == (1, 0, 0)


@pytest.mark.parametrize(
    "fc, status",
    [
        (FailureClass.TIMEOUT, "TIMEOUT"),
        (FailureClass.MODEL_NOT_FOUND, "404"),
        (FailureClass.AUTHENTICATION, "401"),
        (FailureClass.SCHEMA_ERROR, "200"),
    ],
)
def test_a_groq_failure_falls_over_to_cloudflare_only(decided, fc, status):
    router, _, fakes = decided(groq=[failure(fc, status)])
    res = run(router)
    assert res.provider == "cloudflare"
    assert fakes["nvidia"].calls == 0
    assert [a["provider"] for a in res.attempts] == ["groq", "cloudflare"]


def test_when_groq_and_cloudflare_both_fail_nvidia_is_not_tried(decided):
    router, _, fakes = decided(
        groq=[failure(FailureClass.TIMEOUT, "TIMEOUT")],
        cloudflare=[failure(FailureClass.MODEL_NOT_FOUND, "404")],
    )
    with pytest.raises(ModelExecutionError):
        run(router)
    assert fakes["nvidia"].calls == 0
    assert fakes["groq"].calls == 1 and fakes["cloudflare"].calls == 1


def test_the_request_deadline_bounds_a_hanging_groq(decided):
    """Groq hangs for 5 s under a 0.3 s deadline: it is cancelled at the deadline. Whether the
    instant Cloudflare fake still fits into the time left is a race, so either outcome is
    accepted; what is fixed is the bound on the whole request and that NVIDIA is never tried."""
    router, _, fakes = decided(groq_delay=5.0, deadline=0.3)
    start = time.monotonic()
    try:
        assert run(router).provider == "cloudflare"
    except ModelExecutionError as exc:
        assert exc.failure_class == FailureClass.TIMEOUT
    assert time.monotonic() - start < 2.0
    assert fakes["groq"].calls == 1 and fakes["nvidia"].calls == 0


def test_cloudflare_stays_registered_and_the_ignored_flag_is_logged(decided, caplog):
    _, config, _ = decided()
    assert "cloudflare" in [p["provider"] for p in config["order"]]
    assert "CLOUDFLARE_ENABLED=false is not read by the live application" in caplog.text
