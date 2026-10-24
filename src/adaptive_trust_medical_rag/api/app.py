"""
FastAPI application factory for Adaptive Trust Medical RAG.

Registers all routers, middleware, and startup/shutdown lifecycle events.

Usage:
    uvicorn adaptive_trust_medical_rag.api.app:create_app --factory --reload

Or programmatically:
    from adaptive_trust_medical_rag.api.app import create_app
    app = create_app()
"""

from __future__ import annotations

import asyncio
import logging

import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable, Mapping

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from adaptive_trust_medical_rag.api.middleware import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)
from adaptive_trust_medical_rag.api.routes import analyze as analyze_route
from adaptive_trust_medical_rag.api.routes import audit, health, ingest, query
from adaptive_trust_medical_rag.api.schemas import ErrorResponse

log = logging.getLogger(__name__)

# uvicorn configures only its own loggers, so without a handler the package's INFO diagnostics
# (provider order, vision timings) never reach the server console. Records still propagate.
_pkg_log = logging.getLogger("adaptive_trust_medical_rag")
if not _pkg_log.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(levelname)s:     %(name)s: %(message)s"))
    _pkg_log.addHandler(_handler)
    _pkg_log.setLevel(logging.INFO)

_APP_VERSION = "1.0.0"
# Workers AI stops at 256 output tokens by default, which cuts the JSON answer off.
CLOUDFLARE_MAX_TOKENS = 4096
_APP_TITLE = "Adaptive Trust Medical RAG API"
_APP_DESCRIPTION = (
    "Research API for evidence-grounded pharmacological question answering. "
    "NOT for clinical use. All responses are research outputs only."
)


# Repository root: src/adaptive_trust_medical_rag/api/app.py -> parents[3].
REPO_ROOT = Path(__file__).resolve().parents[3]
# Verified available to the project's Groq account on 2026-10-22 (llama-3.3-70b-versatile was not).
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
# Groq model that accepts images; verified on 2026-10-22 to extract the synthetic prescription.
DEFAULT_GROQ_VISION_MODEL = "qwen/qwen3.8-27b"


def load_env_files(root: Path = REPO_ROOT) -> list[str]:
    """Load ``.env.local`` then ``.env`` from the repository root, whatever the working directory.

    Precedence, highest first: variables already in the process environment, then ``.env.local``,
    then ``.env``. A file never overrides a value that is already set. Values are never logged.
    Both files are git-ignored and outside ``frontend/``, so Vite never exposes them to the browser.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return []
    loaded = []
    for name in (".env.local", ".env"):
        path = root / name
        if path.is_file():
            load_dotenv(path, override=False)
            loaded.append(name)
    return loaded


def _env_float(name: str, default: float) -> float:
    try:
        value = float(os.environ.get(name, default))
    except ValueError:
        log.warning("%s is not a number; using %s", name, default)
        return default
    return value if value > 0 else default


LIVE_LLM_PROVIDERS = ("nvidia", "groq", "cloudflare")


def _warn_ignored_provider_settings(fallback_env: str | None) -> None:
    """Say at startup when a provider setting is set but the live router does not read it.

    The live router reads only LLM_FALLBACK_PROVIDERS (plural) and registers only the providers in
    LIVE_LLM_PROVIDERS. A setting the router ignores would otherwise leave a different order in use
    than the one configured, with nothing in the log to say so. This only warns; the order is the
    same with or without it.
    """
    singular = os.environ.get("LLM_FALLBACK_PROVIDER")
    if singular and fallback_env is None:
        log.warning("LLM_FALLBACK_PROVIDER=%s is not read by the live application; it reads "
                    "LLM_FALLBACK_PROVIDERS (comma-separated). Every provider with credentials is used.",
                    singular.strip())
    for name, value in (("LLM_FALLBACK_PROVIDER", singular), ("LLM_FALLBACK_PROVIDERS", fallback_env)):
        for p in (value or "").split(","):
            if p.strip() and p.strip().lower() not in LIVE_LLM_PROVIDERS:
                log.warning("%s names '%s', which the live application has no adapter for; "
                            "supported: %s", name, p.strip(), ", ".join(LIVE_LLM_PROVIDERS))
    if (os.environ.get("CLOUDFLARE_ENABLED", "").strip().lower() == "false"
            and os.environ.get("CLOUDFLARE_API_TOKEN") and os.environ.get("CLOUDFLARE_ACCOUNT_ID")):
        log.warning("CLOUDFLARE_ENABLED=false is not read by the live application; Cloudflare is "
                    "registered because its credentials are set. Unset them to remove it.")


def build_llm_router() -> tuple[Any, dict[str, Any]]:
    """Register every configured LLM provider and order them for failover.

    ``LLM_PROVIDER`` (or ``LLM_PRIMARY_PROVIDER``) names the primary provider. The others follow
    in a fixed order (nvidia, groq, cloudflare), restricted to ``LLM_FALLBACK_PROVIDERS`` when that
    comma-separated list is set; ``LLM_FAILOVER_ENABLED=false`` disables fallback. A provider is
    registered only when its credentials are set, so the order holds no unusable entries. Model IDs
    come from ``GROQ_MODEL`` / ``NVIDIA_LLM_MODEL``; a model the account cannot use fails with
    MODEL_NOT_FOUND on its first request and is never retried. The returned config holds no secrets.
    """
    from adaptive_trust_medical_rag.llm_backend.live_provider_router import LiveProviderRouter
    from adaptive_trust_medical_rag.llm_backend.openai_compatible_backend import (
        DEFAULT_TIMEOUT_S,
        OpenAICompatibleBackend,
    )

    backends: dict[str, Any] = {}
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if groq_api_key:
        backends["groq"] = OpenAICompatibleBackend(
            provider_name="groq",
            base_url=os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            api_key=groq_api_key,
            model_name=os.environ.get("GROQ_MODEL") or DEFAULT_GROQ_MODEL,
            timeout_s=_env_float("GROQ_TIMEOUT_S", DEFAULT_TIMEOUT_S),
        )

    nvidia_llm_api_key = os.environ.get("NVIDIA_LLM_API_KEY") or os.environ.get("NVIDIA_API_KEY")
    if nvidia_llm_api_key:
        backends["nvidia"] = OpenAICompatibleBackend(
            provider_name="nvidia",
            base_url=os.environ.get("NVIDIA_LLM_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            api_key=nvidia_llm_api_key,
            model_name=os.environ.get("NVIDIA_LLM_MODEL", "nvidia/nemotron-3-super-120b-a12b"),
            timeout_s=_env_float("NVIDIA_LLM_TIMEOUT_S", DEFAULT_TIMEOUT_S),
        )

    # HF unstructured API endpoints are not reliable for our schema requirements, so HF_TOKEN
    # registers nothing (it avoids CI hangs and keeps the medical safety JSON gates passing).
    if os.environ.get("CLOUDFLARE_API_TOKEN") and os.environ.get("CLOUDFLARE_ACCOUNT_ID"):
        backends["cloudflare"] = OpenAICompatibleBackend(
            provider_name="cloudflare",
            base_url=f"https://api.cloudflare.com/client/v4/accounts/{os.environ['CLOUDFLARE_ACCOUNT_ID']}/ai/v1",
            api_key=os.environ["CLOUDFLARE_API_TOKEN"],
            model_name=os.environ.get("CLOUDFLARE_MODEL") or "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
            max_tokens=CLOUDFLARE_MAX_TOKENS,
            timeout_s=_env_float("CLOUDFLARE_TIMEOUT_S", DEFAULT_TIMEOUT_S),
        )

    primary = (os.environ.get("LLM_PROVIDER") or os.environ.get("LLM_PRIMARY_PROVIDER") or "nvidia").strip().lower()
    order = [name for name in ("nvidia", "groq", "cloudflare") if name in backends]
    fallback_env = os.environ.get("LLM_FALLBACK_PROVIDERS")
    _warn_ignored_provider_settings(fallback_env)
    if fallback_env is not None:
        allowed = {p.strip().lower() for p in fallback_env.split(",") if p.strip()}
        order = [p for p in order if p == primary or p in allowed]
    if primary in order:
        order.remove(primary)
        order.insert(0, primary)
    elif backends:
        log.error("LLM_PROVIDER=%s is not configured (no credentials); providers in use: %s", primary, order)
    if os.environ.get("LLM_FAILOVER_ENABLED", "true").strip().lower() in ("0", "false", "no"):
        order = order[:1]

    router = LiveProviderRouter(provider_priority=order, deadline_s=_env_float("LLM_REQUEST_DEADLINE_S", 120.0))
    for name, backend in backends.items():
        router.register_provider(name, backend)

    config = {
        "requested_primary": primary,
        "order": router.describe(),
        "deadline_s": router.deadline_s,
        "failover_enabled": len(order) > 1,
    }
    log.info("LLM providers (in order): %s; request deadline %.0f s", config["order"], router.deadline_s)
    return router, config


def requested_workers(argv: list[str] | None = None, env: Mapping[str, str] | None = None) -> int:
    """The worker count asked of uvicorn, read as uvicorn reads it: ``--workers``, else WEB_CONCURRENCY.

    shortcut: a programmatic ``uvicorn.run(workers=N)`` or another server's own option is invisible
    here; the documented command (README) is the supported launch.
    """
    argv = sys.argv if argv is None else argv
    env = os.environ if env is None else env
    for i, arg in enumerate(argv):
        value = argv[i + 1] if arg == "--workers" and i + 1 < len(argv) else (
            arg.split("=", 1)[1] if arg.startswith("--workers=") else None)
        if value is not None and value.isdigit():
            return int(value)
    concurrency = env.get("WEB_CONCURRENCY", "")
    return int(concurrency) if concurrency.isdigit() else 1


def create_app(
    pipeline: Callable | None = None,
    ingester: Callable | None = None,
    db_health_checker: Callable | None = None,
    audit_store: Any | None = None,
    rate_limit: int | None = None,
    rate_window: int = 60,
) -> FastAPI:
    """
    Create and configure the FastAPI application.

    Args:
        pipeline:           RAG pipeline callable (RAGRequest -> RAGResponse).
                            If None, /query returns 503.
        ingester:           Document ingestion callable.
        db_health_checker:  Async callable returning {db: bool, pgvector: bool}.
        audit_store:        Audit log store with get_events(session_id) method.
        rate_limit:         Max requests per IP per window (default: 60, or 10000 in testing).
        rate_window:        Rate limit window in seconds (default: 60).

    Returns:
        Configured FastAPI application instance.
    """

    @asynccontextmanager
    async def lifespan(app_: FastAPI):  # noqa: ANN001
        log.info("Adaptive Trust Medical RAG API v%s starting up", _APP_VERSION)
        # An upload, its stream, its confirmation and its cancel must reach the process that holds the
        # request (app.state.pending_analyses): a second worker would break them silently.
        workers = requested_workers()
        if workers > 1:
            raise RuntimeError(f"This API keeps analysis requests in process memory and supports one worker; "
                               f"it was started with {workers}. Start it with --workers 1.")
        if os.getenv("TESTING") != "1":
            # Load the embedding and NLI models in the background, so the first analysis does not
            # wait ~20 s for them; a request arriving earlier waits on the same load (one copy).
            from adaptive_trust_medical_rag.services.live_application import _lazy_init_models
            asyncio.get_running_loop().run_in_executor(None, _lazy_init_models, app_.state)
        yield
        log.info("Adaptive Trust Medical RAG API shutting down")

    app = FastAPI(
        title=_APP_TITLE,
        lifespan=lifespan,
        description=_APP_DESCRIPTION,
        version=_APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── Middleware (applied last-to-first) ────────────────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)

    effective_rate_limit = rate_limit
    if effective_rate_limit is None:
        effective_rate_limit = 10000 if os.getenv("TESTING") == "1" else 60

    if effective_rate_limit > 0:
        app.add_middleware(RateLimitMiddleware, limit=effective_rate_limit, window=rate_window)
    app.add_middleware(RequestIDMiddleware)
    # CORS for frontend dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Application state ─────────────────────────────────────────────────────
    app.state.pipeline = pipeline
    app.state.ingester = ingester
    app.state.db_health_checker = db_health_checker
    app.state.audit_store = audit_store
    app.state.start_time = time.monotonic()
    app.state.pending_analyses = {}

    # Initialize real components for live app
    from adaptive_trust_medical_rag.normalization.drug_normalizer import DrugNormalizer
    app.state.drug_normalizer = DrugNormalizer(use_api=True)

    load_env_files()

    # Separate NVIDIA credentials: LLM text-generation vs. OCR / Vision extraction
    nvidia_ocr_api_key = (
        os.environ.get("NVIDIA_OCR_API_KEY")
        or os.environ.get("NVIDIA_VISION_API_KEY")
        or os.environ.get("NVIDIA_API_KEY")
    )
    nvidia_ocr_model = (
        os.environ.get("NVIDIA_OCR_MODEL")
        or os.environ.get("NVIDIA_VISION_MODEL")
        or "meta/llama-3.2-11b-vision-instruct"
    )
    nvidia_ocr_base_url = (
        os.environ.get("NVIDIA_OCR_BASE_URL")
        or os.environ.get("NVIDIA_VISION_BASE_URL")
        or "https://integrate.api.nvidia.com/v1"
    )

    router, llm_config = build_llm_router()
    app.state.llm_config = llm_config

    if nvidia_ocr_api_key:
        from adaptive_trust_medical_rag.llm_backend.openai_vision_backend import (
            DEFAULT_VISION_DEADLINE_S,
            DEFAULT_VISION_TIMEOUT_S,
            OpenAIVisionBackend,
        )
        # Groq's image-capable model is tried only after NVIDIA's attempts fail on availability.
        # Verified on 2026-10-22 to read the synthetic prescription; GROQ_VISION_MODEL="" disables it.
        groq_vision_model = os.environ.get("GROQ_VISION_MODEL", DEFAULT_GROQ_VISION_MODEL)
        groq_vision = None
        if os.environ.get("GROQ_API_KEY") and groq_vision_model:
            groq_vision = OpenAIVisionBackend(
                provider_name="groq_vision",
                base_url=os.environ.get("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
                api_key=os.environ["GROQ_API_KEY"],
                model_name=groq_vision_model,
                timeout_s=_env_float("VISION_TIMEOUT_S", DEFAULT_VISION_TIMEOUT_S),
            )
        app.state.vision_backend = OpenAIVisionBackend(
            provider_name="nvidia_vision",
            base_url=nvidia_ocr_base_url,
            api_key=nvidia_ocr_api_key,
            model_name=nvidia_ocr_model,
            # Per-attempt timeout and total deadline; defaults and their basis are in the backend.
            timeout_s=_env_float("VISION_TIMEOUT_S", DEFAULT_VISION_TIMEOUT_S),
            deadline_s=_env_float("VISION_DEADLINE_S", DEFAULT_VISION_DEADLINE_S),
            fallback_model=os.environ.get("VISION_FALLBACK_MODEL") or None,
            fallback_backend=groq_vision,
        )
        log.info("Vision extraction: provider=nvidia_vision model=%s fallback_model=%s fallback_provider=%s",
                 nvidia_ocr_model, os.environ.get("VISION_FALLBACK_MODEL") or None,
                 f"groq_vision/{groq_vision_model}" if groq_vision else None)
    else:
        app.state.vision_backend = None
        log.warning("No vision API key set; prescription image extraction is disabled.")

    if not router.providers:
        log.warning("No LLM API keys set; LLM functionality will be disabled.")
        app.state.llm_backend = None
    else:
        app.state.llm_backend = router

    app.state.claim_verifier = None
    app.state.retrieval_engine = None

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(query.router)
    app.include_router(ingest.router)
    app.include_router(health.router)
    app.include_router(audit.router)
    # Live application route (separate from research evaluation)
    app.include_router(analyze_route.router)

    # ── Global exception handlers ─────────────────────────────────────────────
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error="validation_error",
                detail=str(exc),
                request_id=getattr(request.state, "request_id", None),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        log.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="internal_server_error",
                detail="An unexpected error occurred.",
                request_id=getattr(request.state, "request_id", None),
            ).model_dump(),
        )

    return app


# ── Module-level default instance (for uvicorn) ───────────────────────────────
app = create_app()
