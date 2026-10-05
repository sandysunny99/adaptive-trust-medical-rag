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
import os
import time
from contextlib import asynccontextmanager
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from adaptive_trust_medical_rag.api.middleware import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)
from adaptive_trust_medical_rag.api.routes import audit, health, ingest, query
from adaptive_trust_medical_rag.api.routes import analyze as analyze_route
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
    import os as _os
    if _os.environ.get("GITHUB_ACTIONS") != "true" and _os.environ.get("TESTING") != "1": 
        app.add_middleware(RateLimitMiddleware, limit=rate_limit, window=rate_window)
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
    
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv(".env.local")
        load_dotenv()
    except ImportError:
        pass
        
    groq_api_key = os.environ.get("GROQ_API_KEY")
    nvidia_api_key = os.environ.get("NVIDIA_API_KEY")
    
    from adaptive_trust_medical_rag.llm_backend.openai_compatible_backend import OpenAICompatibleBackend
    from adaptive_trust_medical_rag.llm_backend.live_provider_router import LiveProviderRouter

    primary_provider = os.environ.get("LLM_PROVIDER", "nvidia").lower()
    
    router = LiveProviderRouter(primary_provider=primary_provider, secondary_provider="groq" if primary_provider == "nvidia" else "nvidia")
    
    if groq_api_key:
        groq_backend = OpenAICompatibleBackend(
            provider_name="groq",
            base_url="https://api.groq.com/openai/v1",
            api_key=groq_api_key,
            model_name="openai/gpt-oss-120b"
        )
        router.register_provider("groq", groq_backend)

    if nvidia_api_key:
        nvidia_backend = OpenAICompatibleBackend(
            provider_name="nvidia",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_api_key,
            model_name="nvidia/nemotron-3-super-120b-a12b"
        )
        router.register_provider("nvidia", nvidia_backend)
        
        from adaptive_trust_medical_rag.llm_backend.openai_vision_backend import OpenAIVisionBackend
        app.state.vision_backend = OpenAIVisionBackend(
            provider_name="nvidia_vision",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_api_key,
            model_name="meta/llama-3.2-11b-vision-instruct"
        )
        
    if not router.providers:
        log.warning("No LLM API keys set; LLM functionality will be disabled.")
        app.state.llm_backend = None
        app.state.vision_backend = None
    else:
        app.state.llm_backend = router
        
    from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2
    app.state.claim_verifier = ClaimVerifierV2()
    
    # Load the Live Medical Corpus for the HybridRetrievalEngine
    try:
        from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import HybridRetrievalEngine, Candidate
        import json
        import os
        
        corpus_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "live_medical", "LIVE_MEDICAL_CORPUS_V2.json")
        live_corpus = []
        if os.path.exists(corpus_path):
            with open(corpus_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                live_corpus.append(Candidate(
                    chunk_id=item["chunk_id"],
                    document_id=item["document_id"],
                    text=item["text"],
                    source_url=item.get("document_url", ""),
                    source_authority=item.get("authority", 0.5),
                    metadata={
                        "provenance": item.get("provenance", {}),
                        "freshness_score": item.get("freshness", 0.8),
                        "source_type": item.get("source_type")
                    }
                ))
            
            class LiveEmbeddingModel:
                def __init__(self, data_items):
                    self.text_to_emb = {i["text"]: i["embedding"] for i in data_items if "embedding" in i}
                    from sentence_transformers import SentenceTransformer
                    self.model = SentenceTransformer("all-MiniLM-L6-v2")
                    
                def encode(self, texts):
                    results = []
                    texts_to_compute = []
                    indices_to_compute = []
                    for i, t in enumerate(texts):
                        if t in self.text_to_emb:
                            results.append(self.text_to_emb[t])
                        else:
                            results.append(None)
                            texts_to_compute.append(t)
                            indices_to_compute.append(i)
                    if texts_to_compute:
                        computed = self.model.encode(texts_to_compute).tolist()
                        for i, idx in enumerate(indices_to_compute):
                            results[idx] = computed[i]
                    return results

            app.state.retrieval_engine = HybridRetrievalEngine(live_corpus, LiveEmbeddingModel(data))
            log.info("Loaded real HybridRetrievalEngine with %d chunks.", len(live_corpus))
        else:
            app.state.retrieval_engine = HybridRetrievalEngine([], None)
            log.warning("No live corpus found, initialized empty engine.")
    except Exception as e:
        log.warning("Could not initialize live retrieval engine: %s", e)
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
