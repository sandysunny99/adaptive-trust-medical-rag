"""Ordered LLM provider routing for the live application.

Failure policy (one row per FailureClass; retrying the same provider and switching provider are
decided separately):

    class                 retry same provider        switch to the next provider
    TRANSIENT_PROVIDER    yes, bounded (last only)   yes
    TIMEOUT               yes, bounded (last only)   yes
    NETWORK / CAPACITY    yes, bounded (last only)   yes
    RATE_LIMIT            only within Retry-After    yes
    MODEL_NOT_FOUND       no                         yes  (the model is missing, not slow)
    AUTHENTICATION/-ZATION no                        yes  (each provider has its own key)
    SCHEMA_ERROR          no                         yes  (another model may answer validly)
    INVALID_REQUEST       no                         no   (another provider gets the same request)
    APPLICATION_SEMANTIC  no                         no
    UNKNOWN               no                         no

A failing provider is retried only in automatic mode and only when no eligible provider is left to
switch to: moving on is quicker than waiting on a struggling provider. Every attempt shares one request deadline, and an
attempt still running at the deadline is cancelled. When every attempt fails the router raises
ALL_PROVIDERS_FAILED with the failure class of the last attempt and the full attempt list, so the
first provider's error is never lost. A provider the user selected directly gets one attempt: no retry and no failover.
Each attempt is logged (provider, model, class, status, decision), never a key or the prompt.
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict

from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_backend.interfaces import ProviderAdapter, ProviderResponse
from adaptive_trust_medical_rag.llm_routing.types import FailureClass

log = logging.getLogger(__name__)

DEFAULT_DEADLINE_S = 120.0
MAX_SAME_PROVIDER_RETRIES = 1
BACKOFF_BASE_S = 0.5
# A Retry-After longer than this is not waited for; the request fails over or fails instead.
MAX_RETRY_AFTER_S = 10.0


@dataclass(frozen=True)
class FailurePolicy:
    retry_same: bool
    failover: bool


FAILURE_POLICY: dict[FailureClass, FailurePolicy] = {
    FailureClass.TRANSIENT_PROVIDER: FailurePolicy(True, True),
    FailureClass.TIMEOUT: FailurePolicy(True, True),
    FailureClass.NETWORK: FailurePolicy(True, True),
    FailureClass.CAPACITY: FailurePolicy(True, True),
    FailureClass.RATE_LIMIT: FailurePolicy(True, True),
    FailureClass.MODEL_NOT_FOUND: FailurePolicy(False, True),
    FailureClass.AUTHENTICATION: FailurePolicy(False, True),
    FailureClass.AUTHORIZATION: FailurePolicy(False, True),
    FailureClass.SCHEMA_ERROR: FailurePolicy(False, True),
    FailureClass.INVALID_REQUEST: FailurePolicy(False, False),
    FailureClass.APPLICATION_SEMANTIC: FailurePolicy(False, False),
    FailureClass.UNKNOWN: FailurePolicy(False, False),
}


def policy_for(failure_class: Any) -> FailurePolicy:
    return FAILURE_POLICY.get(failure_class, FAILURE_POLICY[FailureClass.UNKNOWN])


def _failure_class(e: Exception) -> FailureClass:
    fc = getattr(e, "failure_class", FailureClass.UNKNOWN)
    return fc if isinstance(fc, FailureClass) else FailureClass.UNKNOWN


def _deadline_from_env() -> float:
    try:
        value = float(os.environ.get("LLM_REQUEST_DEADLINE_S", DEFAULT_DEADLINE_S))
    except ValueError:
        return DEFAULT_DEADLINE_S
    return value if value > 0 else DEFAULT_DEADLINE_S


class LiveProviderRouter:
    def __init__(
        self,
        provider_priority: list[str] | None = None,
        primary_provider: str | None = None,
        secondary_provider: str | None = None,
        deadline_s: float | None = None,
        sleep: Callable[[float], Awaitable[Any]] | None = None,
    ):
        if provider_priority is not None:
            self.provider_priority = list(provider_priority)
        else:
            self.provider_priority = []
            if primary_provider:
                self.provider_priority.append(primary_provider)
            if secondary_provider and secondary_provider != primary_provider:
                self.provider_priority.append(secondary_provider)
        self.providers: Dict[str, ProviderAdapter] = {}
        # Providers whose model this account cannot use (MODEL_NOT_FOUND, AUTH*), with the class.
        # shortcut: kept in memory until restart, so a model the account gains later needs a restart.
        self.unavailable: Dict[str, str] = {}
        self.deadline_s = deadline_s if deadline_s is not None else _deadline_from_env()
        self._sleep = sleep or asyncio.sleep

    def register_provider(self, name: str, adapter: ProviderAdapter) -> None:
        self.providers[name] = adapter

    def describe(self) -> list[dict[str, Any]]:
        """The effective provider order with each model, for startup logs and diagnostics."""
        order = self.provider_priority or list(self.providers)
        out = []
        for name in order:
            adapter = self.providers.get(name)
            if adapter is None:
                continue
            meta = adapter.get_model_metadata() if hasattr(adapter, "get_model_metadata") else {}
            out.append({"provider": name, "model": meta.get("model") if isinstance(meta, dict) else None})
        return out

    async def generate_structured(
        self,
        prompt: str,
        response_format: Dict[str, Any],
        provider_name: str | None = None,
    ) -> ProviderResponse:
        # A provider the user selected is used alone: no failover to a model they did not choose.
        if provider_name:
            if provider_name not in self.providers:
                raise ModelExecutionError(
                    f"Requested LLM provider '{provider_name}' is not registered or configured.",
                    status_code="PROVIDER_NOT_FOUND",
                )
            log.info("Direct generation with user-selected provider: %s", provider_name)
            order = [provider_name]
            allow_retry = False
        else:
            allow_retry = True
            order = [p for p in (self.provider_priority or list(self.providers)) if p in self.providers]
            usable = [p for p in order if p not in self.unavailable]
            # A provider known to be unusable is skipped while another remains.
            order = usable or order
            missing = [p for p in self.provider_priority if p not in self.providers]
            if missing:
                log.warning("Providers in the priority list but not registered: %s", missing)
        if not order:
            raise ModelExecutionError("No providers available", status_code="NO_PROVIDERS")
        return await self._run(order, prompt, response_format, allow_retry)

    async def _run(self, order: list[str], prompt: str, response_format: Dict[str, Any],
                   allow_retry: bool = True) -> ProviderResponse:
        start = time.monotonic()
        deadline = start + self.deadline_s
        attempts: list[dict[str, Any]] = []
        last_error: ModelExecutionError | None = None

        for index, name in enumerate(order):
            adapter = self.providers[name]
            model = None
            if hasattr(adapter, "get_model_metadata"):
                meta = adapter.get_model_metadata()
                model = meta.get("model") if isinstance(meta, dict) else None
            is_last = index == len(order) - 1
            retries = 0
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    last_error = self._deadline_error(attempts, last_error)
                    raise last_error
                t0 = time.monotonic()
                log.info("Attempting generation with provider: %s (model=%s)", name, model)
                try:
                    response = await asyncio.wait_for(
                        adapter.generate_structured(prompt, response_format), timeout=remaining)
                except asyncio.TimeoutError:
                    err = ModelExecutionError(
                        f"{name} did not answer within the {self.deadline_s:.0f} s request deadline",
                        status_code="DEADLINE_EXCEEDED")
                    err.failure_class = FailureClass.TIMEOUT
                except ModelExecutionError as e:
                    err = e
                else:
                    attempts.append(self._attempt(name, model, t0, outcome="success"))
                    try:
                        response.attempts = attempts
                    except AttributeError:
                        pass
                    if len(attempts) > 1:
                        log.warning("Generation served by %s after %d failed attempt(s)", name, len(attempts) - 1)
                    return response

                fc = _failure_class(err)
                policy = policy_for(fc)
                retry_after = getattr(err, "retry_after", None)
                can_retry = (allow_retry and policy.retry_same and is_last and retries < MAX_SAME_PROVIDER_RETRIES)
                if fc == FailureClass.RATE_LIMIT:
                    can_retry = can_retry and retry_after is not None and retry_after <= MAX_RETRY_AFTER_S
                if can_retry:
                    delay = retry_after if retry_after is not None else BACKOFF_BASE_S * (2 ** retries)
                    delay += random.uniform(0, BACKOFF_BASE_S / 2)  # noqa: S311  # nosec B311 (retry jitter)
                    can_retry = delay < deadline - time.monotonic()
                decision = ("retry_same" if can_retry else
                            "failover" if policy.failover and not is_last else
                            "stop")
                attempts.append(self._attempt(name, model, t0, outcome="failed", failure_class=fc.value,
                                              status_code=getattr(err, "status_code", None), decision=decision))
                permanent = fc in (FailureClass.AUTHENTICATION, FailureClass.AUTHORIZATION,
                                   FailureClass.MODEL_NOT_FOUND)
                if permanent:
                    self.unavailable[name] = fc.value
                level = logging.ERROR if permanent else logging.WARNING
                log.log(level, "Provider %s (model=%s) failed: class=%s status=%s decision=%s",
                        name, model, fc.value, getattr(err, "status_code", None), decision)
                last_error = err
                if decision == "retry_same":
                    retries += 1
                    await self._sleep(delay)
                    continue
                break

            if not policy.failover:
                # Another provider cannot fix this failure, so it is reported as it is.
                self._attach(last_error, attempts)
                raise last_error

        if len(order) == 1:
            # One provider (or a direct selection): its own error is the accurate report.
            self._attach(last_error, attempts)
            raise last_error
        raise self._all_failed(attempts, last_error)

    @staticmethod
    def _attempt(name: str, model: Any, t0: float, **fields: Any) -> dict[str, Any]:
        return {"provider": name, "model": model, "elapsed_ms": round((time.monotonic() - t0) * 1000, 1), **fields}

    @staticmethod
    def _attach(err: ModelExecutionError, attempts: list[dict[str, Any]]) -> None:
        try:
            err.attempts = list(attempts)
        except AttributeError:
            pass

    def _deadline_error(self, attempts: list[dict[str, Any]], last: ModelExecutionError | None) -> ModelExecutionError:
        err = ModelExecutionError(
            f"LLM request deadline of {self.deadline_s:.0f} s exceeded after {len(attempts)} attempt(s)"
            + (f"; last error: {last}" if last else ""),
            status_code="DEADLINE_EXCEEDED")
        err.failure_class = FailureClass.TIMEOUT
        err.attempts = list(attempts)
        return err

    @staticmethod
    def _all_failed(attempts: list[dict[str, Any]], last: ModelExecutionError | None) -> ModelExecutionError:
        summary = "; ".join(f"{a['provider']}: {a.get('failure_class')} ({a.get('status_code')})" for a in attempts)
        err = ModelExecutionError(f"All LLM providers failed ({summary}). Last error: {last}",
                                  status_code="ALL_PROVIDERS_FAILED")
        err.failure_class = _failure_class(last) if last else FailureClass.UNKNOWN
        err.attempts = list(attempts)
        err.__cause__ = last
        return err
