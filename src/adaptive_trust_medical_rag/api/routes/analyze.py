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

from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException
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
from adaptive_trust_medical_rag.services.image_validator import ImageValidator, ImageValidationError

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

@router.post(
    "/analyze/prescription",
    summary="Upload a prescription image for extraction and analysis",
)
async def post_analyze_prescription(
    request: Request,
    image: UploadFile = File(...),
    patient_context: str = Form(None)
):
    """
    Accept a prescription image upload.
    Validates the image and queues it for extraction.
    """
    try:
        file_bytes = await image.read()
        validation_meta = ImageValidator.validate_and_preprocess(
            file_bytes=file_bytes,
            filename=image.filename,
            content_type=image.content_type
        )
    except ImageValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        log.error(f"Image processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during image validation")

    request_id = str(uuid.uuid4())
    
    pending = getattr(request.app.state, "pending_analyses", None)
    if pending is None:
        request.app.state.pending_analyses = {}
        pending = request.app.state.pending_analyses

    # Parse patient context if provided
    context_data = None
    if patient_context:
        try:
            context_data = json.loads(patient_context)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid patient_context JSON")

    pending[request_id] = {
        "type": "prescription_image",
        "image_bytes": file_bytes,
        "image_meta": validation_meta,
        "patient_context": context_data,
        "created_at": time.time(),
    }

    log.info(f"POST /api/v1/analyze/prescription request_id={request_id} size={len(file_bytes)}")

    return {
        "request_id": request_id,
        "stream_url": f"/api/v1/stream/{request_id}",
        "validation": validation_meta
    }

from pydantic import BaseModel
from typing import Optional

class ConfirmedMedicationItem(BaseModel):
    name: str
    status: str
    source: str
    raw_detected_name: Optional[str] = None

class ConfirmMedicationsRequest(BaseModel):
    confirmed_medications: list[ConfirmedMedicationItem]

@router.post(
    "/analyze/{request_id}/confirm",
    summary="Confirm medications for analysis",
)
async def confirm_medications(request_id: str, body: ConfirmMedicationsRequest, request: Request):
    pending = getattr(request.app.state, "pending_analyses", {})
    analysis = pending.get(request_id)
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis request not found or expired")
        
    analysis["confirmed_medications"] = body.confirmed_medications
    if "confirmation_event" in analysis:
        analysis["confirmation_event"].set()
        
    return {"status": "success", "confirmed": body.confirmed_medications}

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

    async def pipeline_stream():
        """Execute the analysis pipeline and emit SSE events."""
        start_time = time.time()
        
        try:
            from adaptive_trust_medical_rag.services.live_application import LiveMedicalRAGService
            service = LiveMedicalRAGService(request.app.state)
            
            # Support both direct_drugs and prescription_image
            drug_names = []
            patient_context_dict = None
            image_bytes = None
            image_meta = None
            
            if analysis.get("type") == "prescription_image":
                image_bytes = analysis.get("image_bytes")
                image_meta = analysis.get("image_meta")
                patient_context_dict = analysis.get("patient_context")
                # Create an event to wait for confirmation
                analysis["confirmation_event"] = asyncio.Event()
            else:
                body: AnalyzeRequest = analysis["body"]
                drug_names = body.drug_names
                patient_context_dict = body.patient_context.model_dump() if body.patient_context else None

            async for event_dict in service.execute(
                request_id=request_id,
                drug_names=drug_names,
                patient_context=patient_context_dict,
                start_time=start_time,
                image_bytes=image_bytes,
                image_meta=image_meta,
                analysis_state=analysis
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
