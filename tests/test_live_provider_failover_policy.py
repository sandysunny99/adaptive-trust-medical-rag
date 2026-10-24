"""Provider failure classification, retry and failover policy, and LLM configuration.

Retrying the same provider and switching provider are decided separately (see
live_provider_router.FAILURE_POLICY). Fake adapters reproduce each failure deterministically;
none of these tests calls a real provider.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from adaptive_trust_medical_rag.api import app as app_module
from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_backend.interfaces import ProviderResponse
from adaptive_trust_medical_rag.llm_backend.live_provider_router import FAILURE_POLICY, LiveProviderRouter
from adaptive_trust_medical_rag.llm_backend.openai_compatible_backend import OpenAICompatibleBackend
from adaptive_trust_medical_rag.llm_routing.types import FailureClass

FAKE_KEY = "FAKE_TEST_KEY_NOT_A_SECRET_0000"


def ok(provider: str) -> ProviderResponse:
    return ProviderResponse(provider=provider, model=f"{provider}-model", request_id="r", content="{}",
                            structured_output={}, usage={}, latency_ms=1.0, finish_reason="stop",
                            transport_status=200, raw_metadata={})


def failure(fc: FailureClass, status: str = "X", retry_after: float | None = None) -> ModelExecutionError:
    err = ModelExecutionError(f"simulated {fc.value}", status_code=status)
    err.failure_class = fc
    if retry_after is not None:
        err.retry_after = retry_after
    return err


class Adapter:
    """Fails with the given errors in turn, then succeeds."""

    def __init__(self, name: str, *errors: Exception, delay: float = 0.0):
        self.name, self.errors, self.delay, self.calls = name, list(errors), delay, 0
        self.cancelled = False

    def get_model_metadata(self):
        return {"provider": self.name, "model": f"{self.name}-model"}

    async def generate_structured(self, prompt, response_format):
        self.calls += 1
        if self.delay:
            try:
                await asyncio.sleep(self.delay)
            except asyncio.CancelledError:
                self.cancelled = True
                raise
        if self.errors:
            raise self.errors.pop(0)
        return ok(self.name)


def router(*adapters: Adapter, deadline_s: float = 30.0) -> tuple[LiveProviderRouter, list[float]]:
    slept: list[float] = []

    async def fake_sleep(seconds):
        slept.append(seconds)

    r = LiveProviderRouter(provider_priority=[a.name for a in adapters], deadline_s=deadline_s, sleep=fake_sleep)
    for a in adapters:
        r.register_provider(a.name, a)
    return r, slept


def generate(r: LiveProviderRouter, **kwargs):
    return asyncio.run(r.generate_structured("prompt", {"type": "json_object"}, **kwargs))


# ── Policy table ─────────────────────────────────────────────────────────────

def test_every_failure_class_has_an_explicit_policy():
    assert set(FAILURE_POLICY) == set(FailureClass)


@pytest.mark.parametrize("fc", [FailureClass.MODEL_NOT_FOUND, FailureClass.AUTHENTICATION,
                                FailureClass.INVALID_REQUEST, FailureClass.SCHEMA_ERROR,
                                FailureClass.APPLICATION_SEMANTIC, FailureClass.UNKNOWN])
def test_permanent_failures_are_never_retried_on_the_same_provider(fc):
    assert FAILURE_POLICY[fc].retry_same is False


# ── Test C: model not found ──────────────────────────────────────────────────

def test_model_not_found_fails_over_once_without_retrying_the_missing_model():
    nvidia = Adapter("nvidia", failure(FailureClass.MODEL_NOT_FOUND, "404"))
    groq = Adapter("groq")
    r, slept = router(nvidia, groq)
    res = generate(r)
    assert res.provider == "groq"
    assert (nvidia.calls, groq.calls, slept) == (1, 1, [])
    assert [(a["provider"], a.get("failure_class"), a.get("decision"), a["outcome"]) for a in res.attempts] == [
        ("nvidia", "MODEL_NOT_FOUND", "failover", "failed"), ("groq", None, None, "success")]


def test_model_not_found_on_the_last_provider_is_reported_without_a_retry():
    groq = Adapter("groq", failure(FailureClass.MODEL_NOT_FOUND, "404"), failure(FailureClass.MODEL_NOT_FOUND, "404"))
    r, slept = router(groq)
    with pytest.raises(ModelExecutionError) as exc:
        generate(r)
    assert exc.value.failure_class == FailureClass.MODEL_NOT_FOUND
    assert (groq.calls, slept) == (1, [])


# ── Test D: transient failures ───────────────────────────────────────────────

def test_a_timeout_fails_over_immediately_when_a_fallback_exists():
    nvidia = Adapter("nvidia", failure(FailureClass.TIMEOUT, "TIMEOUT"))
    groq = Adapter("groq")
    r, slept = router(nvidia, groq)
    assert generate(r).provider == "groq"
    assert (nvidia.calls, slept) == (1, [])


def test_a_transient_failure_on_the_last_provider_gets_one_bounded_retry_with_backoff():
    groq = Adapter("groq", failure(FailureClass.TRANSIENT_PROVIDER, "503"))
    r, slept = router(groq)
    res = generate(r)
    assert res.provider == "groq" and groq.calls == 2
    assert len(slept) == 1 and 0.5 <= slept[0] <= 0.75
    assert [a.get("decision") for a in res.attempts] == ["retry_same", None]


def test_a_persistent_transient_failure_stops_after_the_bounded_retry():
    groq = Adapter("groq", *[failure(FailureClass.TRANSIENT_PROVIDER, "503")] * 5)
    r, _ = router(groq)
    with pytest.raises(ModelExecutionError) as exc:
        generate(r)
    assert groq.calls == 2
    assert [a["decision"] for a in exc.value.attempts] == ["retry_same", "stop"]


def test_rate_limit_waits_only_for_a_short_retry_after():
    short = Adapter("groq", failure(FailureClass.RATE_LIMIT, "429", retry_after=2))
    r, slept = router(short)
    assert generate(r).provider == "groq" and short.calls == 2 and 2 <= slept[0] < 2.3

    long = Adapter("groq", failure(FailureClass.RATE_LIMIT, "429", retry_after=60))
    r, slept = router(long)
    with pytest.raises(ModelExecutionError):
        generate(r)
    assert (long.calls, slept) == (1, [])


def test_the_request_deadline_cancels_a_hanging_provider():
    slow = Adapter("nvidia", delay=5.0)
    r, _ = router(slow, deadline_s=0.2)
    with pytest.raises(ModelExecutionError) as exc:
        generate(r)
    assert exc.value.failure_class == FailureClass.TIMEOUT
    assert slow.cancelled is True


def test_the_deadline_is_shared_across_providers():
    slow = Adapter("nvidia", delay=5.0)
    groq = Adapter("groq")
    r, _ = router(slow, groq, deadline_s=0.2)
    with pytest.raises(ModelExecutionError) as exc:
        generate(r)
    # nvidia used the whole budget; groq is never started after the deadline.
    assert exc.value.status_code == "DEADLINE_EXCEEDED" and groq.calls == 0


# ── Test E: authentication and invalid requests ─────────────────────────────

def test_authentication_failure_moves_to_an_independently_configured_provider():
    nvidia = Adapter("nvidia", failure(FailureClass.AUTHENTICATION, "401"))
    groq = Adapter("groq")
    r, slept = router(nvidia, groq)
    res = generate(r)
    assert res.provider == "groq" and nvidia.calls == 1 and slept == []
    assert res.attempts[0]["failure_class"] == "AUTHENTICATION"


def test_an_invalid_request_is_not_sent_to_another_provider():
    nvidia = Adapter("nvidia", failure(FailureClass.INVALID_REQUEST, "400"))
    groq = Adapter("groq")
    r, _ = router(nvidia, groq)
    with pytest.raises(ModelExecutionError) as exc:
        generate(r)
    assert exc.value.failure_class == FailureClass.INVALID_REQUEST and groq.calls == 0


def test_a_direct_selection_gets_one_attempt_and_no_failover():
    nvidia = Adapter("nvidia", failure(FailureClass.TIMEOUT, "TIMEOUT"))
    groq = Adapter("groq")
    r, slept = router(nvidia, groq)
    with pytest.raises(ModelExecutionError):
        generate(r, provider_name="nvidia")
    assert (nvidia.calls, groq.calls, slept) == (1, 0, [])


# ── Test F: every provider fails ─────────────────────────────────────────────

def test_when_every_provider_fails_the_first_error_is_kept_and_nothing_succeeds():
    nvidia = Adapter("nvidia", failure(FailureClass.MODEL_NOT_FOUND, "404"))
    groq = Adapter("groq", failure(FailureClass.AUTHENTICATION, "401"))
    r, _ = router(nvidia, groq)
    with pytest.raises(ModelExecutionError) as exc:
        generate(r)
    err = exc.value
    assert err.status_code == "ALL_PROVIDERS_FAILED"
    assert [(a["provider"], a["failure_class"]) for a in err.attempts] == [
        ("nvidia", "MODEL_NOT_FOUND"), ("groq", "AUTHENTICATION")]
    assert "nvidia: MODEL_NOT_FOUND" in str(err)


# ── Adapter classification (real HTTP responses are simulated) ──────────────

class Resp:
    def __init__(self, status, text="", headers=None, body=None):
        self.status_code, self.text, self.headers, self._body = status, text, headers or {}, body

    def json(self):
        return self._body


def backend_error(status, text, headers=None):
    backend = OpenAICompatibleBackend("nvidia", "https://example.invalid/v1", FAKE_KEY, "nvidia/some-model")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as post:
        post.return_value = Resp(status, text, headers)
        with pytest.raises(ModelExecutionError) as exc:
            asyncio.run(backend.generate_structured("p", {"type": "json_object"}))
    return exc.value


def test_a_404_is_model_not_found_not_a_transient_outage():
    err = backend_error(404, "Function 'x': Not found for account 'y'")
    assert err.failure_class == FailureClass.MODEL_NOT_FOUND
    assert "nvidia/some-model" in str(err) and "check the configured model ID" in str(err)


def test_groq_json_validate_failed_is_a_malformed_output_not_a_bad_request():
    err = backend_error(400, '{"error":{"code":"json_validate_failed"}}')
    assert err.failure_class == FailureClass.SCHEMA_ERROR


def test_retry_after_is_read_and_the_key_never_appears_in_the_error():
    err = backend_error(429, f"slow down {FAKE_KEY}", headers={"retry-after": "3"})
    assert err.failure_class == FailureClass.RATE_LIMIT and err.retry_after == 3.0
    assert FAKE_KEY not in str(err)


def test_an_empty_choice_list_is_a_malformed_response():
    backend = OpenAICompatibleBackend("groq", "https://example.invalid/v1", FAKE_KEY, "m")
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as post:
        post.return_value = Resp(200, body={"choices": []})
        with pytest.raises(ModelExecutionError) as exc:
            asyncio.run(backend.generate_structured("p", {}))
    assert exc.value.failure_class == FailureClass.SCHEMA_ERROR


# ── Test A: configuration ───────────────────────────────────────────────────

LLM_ENV = ("LLM_PROVIDER", "LLM_PRIMARY_PROVIDER", "LLM_FALLBACK_PROVIDERS", "LLM_FAILOVER_ENABLED",
           "GROQ_API_KEY", "GROQ_MODEL", "NVIDIA_LLM_API_KEY", "NVIDIA_API_KEY", "NVIDIA_LLM_MODEL",
           "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID", "LLM_REQUEST_DEADLINE_S")


@pytest.fixture
def clean_env(monkeypatch):
    for k in LLM_ENV:
        monkeypatch.delenv(k, raising=False)
    return monkeypatch


def test_llm_provider_groq_puts_groq_first_with_the_verified_default_model(clean_env):
    clean_env.setenv("LLM_PROVIDER", "groq")
    clean_env.setenv("GROQ_API_KEY", FAKE_KEY)
    clean_env.setenv("NVIDIA_API_KEY", FAKE_KEY)
    r, config = app_module.build_llm_router()
    assert config["order"] == [{"provider": "groq", "model": "openai/gpt-oss-120b"},
                               {"provider": "nvidia", "model": "nvidia/nemotron-3-super-120b-a12b"}]
    assert FAKE_KEY not in repr(config)


def test_groq_model_comes_from_the_environment(clean_env):
    clean_env.setenv("GROQ_API_KEY", FAKE_KEY)
    clean_env.setenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    r, _ = app_module.build_llm_router()
    assert r.providers["groq"].model_name == "qwen/qwen3.8-27b"


def test_failover_can_be_disabled_or_restricted(clean_env):
    for k in ("GROQ_API_KEY", "NVIDIA_API_KEY", "CLOUDFLARE_API_TOKEN"):
        clean_env.setenv(k, FAKE_KEY)
    clean_env.setenv("CLOUDFLARE_ACCOUNT_ID", "acct")
    clean_env.setenv("LLM_PROVIDER", "groq")
    clean_env.setenv("LLM_FALLBACK_PROVIDERS", "cloudflare")
    _, config = app_module.build_llm_router()
    assert [p["provider"] for p in config["order"]] == ["groq", "cloudflare"]
    clean_env.setenv("LLM_FAILOVER_ENABLED", "false")
    _, config = app_module.build_llm_router()
    assert [p["provider"] for p in config["order"]] == ["groq"] and config["failover_enabled"] is False


def test_an_unconfigured_primary_is_logged_and_the_configured_providers_are_used(clean_env, caplog):
    clean_env.setenv("LLM_PROVIDER", "groq")
    clean_env.setenv("NVIDIA_API_KEY", FAKE_KEY)
    _, config = app_module.build_llm_router()
    assert [p["provider"] for p in config["order"]] == ["nvidia"]
    assert "LLM_PROVIDER=groq is not configured" in caplog.text


def test_env_files_load_from_the_repo_root_with_process_env_first(clean_env, tmp_path):
    (tmp_path / ".env.local").write_text("LLM_PROVIDER=groq\nGROQ_MODEL=from-local\n", encoding="utf-8")
    (tmp_path / ".env").write_text("LLM_PROVIDER=nvidia\nGROQ_MODEL=from-env\nNVIDIA_LLM_MODEL=from-env\n",
                                   encoding="utf-8")
    clean_env.setenv("GROQ_MODEL", "from-process")
    clean_env.delenv("NVIDIA_LLM_MODEL", raising=False)
    clean_env.chdir(tmp_path.parent)  # the working directory does not matter
    assert app_module.load_env_files(tmp_path) == [".env.local", ".env"]
    import os
    assert os.environ["LLM_PROVIDER"] == "groq"          # .env.local over .env
    assert os.environ["GROQ_MODEL"] == "from-process"    # process environment over both files
    assert os.environ["NVIDIA_LLM_MODEL"] == "from-env"  # .env fills what nothing else set
    clean_env.delenv("NVIDIA_LLM_MODEL")



# ── A model the account cannot use is remembered ────────────────────────────

def test_a_model_not_found_provider_is_skipped_on_the_next_request():
    nvidia = Adapter("nvidia", failure(FailureClass.MODEL_NOT_FOUND, "404"))
    groq = Adapter("groq")
    r, _ = router(nvidia, groq)
    generate(r)
    assert r.unavailable == {"nvidia": "MODEL_NOT_FOUND"}
    res = generate(r)
    assert res.provider == "groq" and nvidia.calls == 1 and [a["provider"] for a in res.attempts] == ["groq"]


def test_a_transient_failure_does_not_mark_a_provider_unusable():
    nvidia = Adapter("nvidia", failure(FailureClass.TIMEOUT, "TIMEOUT"))
    r, _ = router(nvidia, Adapter("groq"))
    generate(r)
    assert r.unavailable == {}


def test_the_model_list_and_manual_selection_report_an_unusable_model(clean_env):
    from adaptive_trust_medical_rag.llm_backend.model_registry import get_available_models, validate_llm_selection
    clean_env.setenv("GROQ_API_KEY", FAKE_KEY)
    clean_env.setenv("NVIDIA_API_KEY", FAKE_KEY)
    r, _ = app_module.build_llm_router()
    state = SimpleNamespace(llm_backend=r)
    nemotron = "nvidia/nemotron-3-super-120b-a12b"
    assert {m["id"]: m["is_available"] for m in get_available_models(state)}[nemotron] is True
    r.unavailable["nvidia"] = "MODEL_NOT_FOUND"
    models = {m["id"]: m["is_available"] for m in get_available_models(state)}
    assert models[nemotron] is False and models["openai/gpt-oss-120b"] is True
    ok, msg, _ = validate_llm_selection({"mode": "manual", "model_id": nemotron}, state)
    assert ok is False and "not available to this account (MODEL_NOT_FOUND)" in msg


def test_cloudflare_model_comes_from_the_environment_with_the_registry_default(clean_env):
    clean_env.setenv("CLOUDFLARE_API_TOKEN", FAKE_KEY)
    clean_env.setenv("CLOUDFLARE_ACCOUNT_ID", "acct")
    clean_env.delenv("CLOUDFLARE_MODEL", raising=False)
    r, _ = app_module.build_llm_router()
    assert r.providers["cloudflare"].model_name == "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
    clean_env.setenv("CLOUDFLARE_MODEL", "@cf/test/other-model")
    r, _ = app_module.build_llm_router()
    assert r.providers["cloudflare"].model_name == "@cf/test/other-model"
