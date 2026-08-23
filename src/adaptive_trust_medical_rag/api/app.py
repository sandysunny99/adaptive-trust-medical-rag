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

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from adaptive_trust_medical_rag.api.middleware import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)
from adaptive_trust_medical_rag.api.routes import audit, health, ingest, query
from adaptive_trust_medical_rag.api.schemas import ErrorResponse

log = logging.getLogger(__name__)

_APP_VERSION = "1.0.0"
_APP_TITLE = "Adaptive Trust Medical RAG API"
_APP_DESCRIPTION = (
    "Research API for evidence-grounded pharmacological question answering. "
    "NOT for clinical use. All responses are research outputs only."
)


def create_app(
    pipeline: Callable | None = None,
    ingester: Callable | None = None,
    db_health_checker: Callable | None = None,
    audit_store: Any | None = None,
    rate_limit: int = 60,
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
        rate_limit:         Max requests per IP per window (default: 60).
        rate_window:        Rate limit window in seconds (default: 60).

    Returns:
        Configured FastAPI application instance.
    """

    @asynccontextmanager
    async def lifespan(app_: FastAPI):  # noqa: ANN001
        log.info("Adaptive Trust Medical RAG API v%s starting up", _APP_VERSION)
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
    app.add_middleware(RateLimitMiddleware, limit=rate_limit, window=rate_window)
    app.add_middleware(RequestIDMiddleware)

    # ── Application state ─────────────────────────────────────────────────────
    app.state.pipeline = pipeline
    app.state.ingester = ingester
    app.state.db_health_checker = db_health_checker
    app.state.audit_store = audit_store
    app.state.start_time = time.monotonic()

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(query.router)
    app.include_router(ingest.router)
    app.include_router(health.router)
    app.include_router(audit.router)

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
