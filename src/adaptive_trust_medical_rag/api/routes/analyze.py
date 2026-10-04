"""POST /api/v1/analyze — live medication analysis endpoint.

This endpoint serves the LIVE APPLICATION mode.
It is completely separate from the research evaluation pipeline.
Live requests are NEVER counted as research evaluation requests.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from adaptive_trust_medical_rag.api.live_schemas import (
    AnalyzeAccepted,
    AnalyzeRequest,
    AnalyzeResponse,
    MedicationResult,
    TrustFactorsResult,
    TrustResult,
    SecurityResult,
    EvidenceResult,
    ClaimResult,
    DrugInteractionResult,
    FoodGuidanceResult,
    PatientConsiderationResult,
    ProvenanceStep,
)
from adaptive_trust_medical_rag.security.sanitizer import sanitize_query

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["live"])


async def _sse_event(event: str, data: dict[str, Any]) -> str:
    """Format a Server-Sent Event."""
    payload = json.dumps(data, default=str)
    return f"event: {event}\ndata: {payload}\n\n"


@router.post(
    "/analyze",
    response_model=AnalyzeAccepted,
    summary="Submit medications for evidence-grounded safety analysis",
)
async def post_analyze(body: AnalyzeRequest, request: Request) -> AnalyzeAccepted:
    """
    Accept a medication analysis request and return a stream URL.

    The analysis runs asynchronously and emits real-time SSE events
    via GET /api/v1/stream/{request_id}.

    **Privacy:** Drug names are sanitized. No PHI accepted.
    **Disclaimer:** Research output only. Not for clinical use.
    """
    request_id = str(uuid.uuid4())

    # Store the pending analysis request in app state
    pending = getattr(request.app.state, "pending_analyses", None)
    if pending is None:
        request.app.state.pending_analyses = {}
        pending = request.app.state.pending_analyses

    pending[request_id] = {
        "body": body,
        "created_at": time.time(),
    }

    log.info(
        "POST /api/v1/analyze request_id=%s drugs=%d mode=%s",
        request_id,
        len(body.drug_names),
        body.input_mode.value,
    )

    return AnalyzeAccepted(
        request_id=request_id,
        stream_url=f"/api/v1/stream/{request_id}",
    )


@router.get(
    "/stream/{request_id}",
    summary="SSE stream for medication analysis pipeline",
)
async def stream_analysis(request_id: str, request: Request) -> StreamingResponse:
    """
    Stream real-time pipeline events for a pending analysis.

    Emits structured SSE events as each pipeline stage completes.
    """
    pending = getattr(request.app.state, "pending_analyses", {})
    analysis = pending.get(request_id)

    if analysis is None:
        async def error_stream():
            yield await _sse_event("error", {
                "code": "NOT_FOUND",
                "message": f"Analysis {request_id} not found or expired.",
            })

        return StreamingResponse(error_stream(), media_type="text/event-stream")

    body: AnalyzeRequest = analysis["body"]

    async def pipeline_stream():
        """Execute the analysis pipeline and emit SSE events."""
        start_time = time.time()
        
        try:
            from adaptive_trust_medical_rag.services.live_application import LiveMedicalRAGService
            service = LiveMedicalRAGService(request.app.state)
            
            async for event_dict in service.execute(
                request_id=request_id,
                drug_names=body.drug_names,
                patient_context=body.patient_context.model_dump() if body.patient_context else None,
                start_time=start_time
            ):
                yield await _sse_event(event_dict["event"], event_dict["data"])
                
        except Exception as e:
            log.error("Pipeline error for %s: %s", request_id, e)
            import traceback
            traceback.print_exc()
            yield await _sse_event("error", {
                "code": "PIPELINE_ERROR",
                "message": str(e),
            })
        finally:
            # Clean up pending analysis
            pending.pop(request_id, None)

    return StreamingResponse(
        pipeline_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _ts() -> str:
    """Current ISO timestamp."""
    from datetime import datetime, UTC
    return datetime.now(UTC).isoformat()


def _elapsed(start: float) -> float:
    """Milliseconds since start."""
    return round((time.time() - start) * 1000, 1)
