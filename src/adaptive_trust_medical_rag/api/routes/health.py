"""GET /health route handler."""

from __future__ import annotations

import time

from fastapi import APIRouter, Request

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
