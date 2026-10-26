"""GET /health route handler."""

from __future__ import annotations

import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from adaptive_trust_medical_rag.api.schemas import HealthResponse

router = APIRouter()
_START_TIME = time.monotonic()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["ops"],
)
async def get_health(request: Request) -> HealthResponse:
    """
    Return service health including database and pgvector status.

    Always returns HTTP 200. Consumers should check the 'status' field:
      - ok:        All systems healthy.
      - degraded:  Database reachable but pgvector missing.
      - unhealthy: Database unreachable.
    """
    uptime = round(time.monotonic() - _START_TIME, 1)

    # Try DB health if checker is available
    db_ok = False
    pgvector_ok = False
    db_checker = getattr(request.app.state, "db_health_checker", None)
    if db_checker is not None:
        try:
            result = await db_checker()
            db_ok = result.get("db", False)
            pgvector_ok = result.get("pgvector", False)
        except Exception:
            db_ok = False
            pgvector_ok = False
    else:
        # No live DB configured (dev / test mode)
        db_ok = False
        pgvector_ok = False

    if db_ok and pgvector_ok:
        overall = "ok"
    elif db_ok:
        overall = "degraded"
    else:
        overall = "unhealthy"

    return HealthResponse(
        status=overall,
        database=db_ok,
        pgvector=pgvector_ok,
        version="1.0.0",
        uptime_seconds=uptime,
        details={"mode": "test" if db_checker is None else "production"},
    )


@router.get("/health/live", summary="Liveness: the process is serving requests", tags=["ops"])
async def get_liveness() -> dict[str, str]:
    """Always 200 while the process answers; says nothing about dependencies."""
    return {"status": "alive"}


@router.get("/health/ready", summary="Readiness of the live application", tags=["ops"])
async def get_readiness(request: Request) -> JSONResponse:
    """200 when the live analysis can run: retrieval and the claim verifier are loaded and an LLM
    provider is configured; 503 with what is missing otherwise (models load in the background at
    startup, so a fresh process is briefly not ready). The live application uses no database, so
    one is not required here; /health still reports the research database. Vision is optional
    (typed medication names work without it). No configuration values are returned."""
    state = request.app.state
    missing = [name for name, ready in (
        ("retrieval", getattr(state, "retrieval_engine", None) is not None),
        ("claim_verifier", getattr(state, "claim_verifier", None) is not None),
        ("llm_provider", getattr(state, "llm_backend", None) is not None),
    ) if not ready]
    errors = getattr(state, "model_init_errors", None) or {}
    body = {
        "status": "not_ready" if missing else "ready",
        "missing": missing,
        "errors": {k: v for k, v in errors.items() if k in missing},
        "vision": "configured" if getattr(state, "vision_backend", None) is not None else "not configured",
        "database": "not used by the live application",
    }
    return JSONResponse(status_code=503 if missing else 200, content=body)
