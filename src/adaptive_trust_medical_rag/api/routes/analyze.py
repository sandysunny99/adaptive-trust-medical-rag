"""POST /api/v1/analyze — live medication analysis endpoint.

This endpoint serves the LIVE APPLICATION mode.
It is completely separate from the research evaluation pipeline.
Live requests are NEVER counted as research evaluation requests.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from adaptive_trust_medical_rag.api.live_schemas import (
    AnalyzeAccepted,
    AnalyzeRequest,
    LLMModelInfo,
    LLMModelsResponse,
    LLMSelectionInput,
    PatientContextInput,
)
from adaptive_trust_medical_rag.llm_backend.model_registry import (
    get_available_models,
    validate_llm_selection,
)
from adaptive_trust_medical_rag.services.image_validator import ImageValidationError, ImageValidator

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["live"])

# A request's stream must open within this long of its submission (the page opens it at once). After
# that the request, uploaded image included, is dropped. Once streaming, the pipeline's own deadlines
# (OCR, vision, the confirmation wait) end it, and a client that drops the stream ends it at once.
STREAM_OPEN_TTL_S = 120.0


def _hold(pending: dict[str, dict[str, Any]], request_id: str, entry: dict[str, Any]) -> None:
    """Keep a submitted request until its stream opens, and drop it at its deadline if it never does.

    The deadline is a timer on the server's loop (monotonic), so an idle server drops it too.
    """
    entry["open_by"] = time.monotonic() + STREAM_OPEN_TTL_S
    pending[request_id] = entry
    asyncio.get_running_loop().call_later(STREAM_OPEN_TTL_S, _drop_if_unopened, pending, request_id)


def _drop_if_unopened(pending: dict[str, dict[str, Any]], request_id: str) -> None:
    analysis = pending.get(request_id)
    if analysis is not None and not analysis.get("streaming"):
        pending.pop(request_id, None)
        log.info("Request %s expired before its stream opened; dropped", request_id)


@router.get(
    "/llm/models",
    response_model=LLMModelsResponse,
    summary="Get available LLM models for medication safety analysis",
)
async def get_llm_models(request: Request) -> LLMModelsResponse:
    """Return catalog of supported answer-generation models and their availability."""
    models_data = get_available_models(request.app.state)
    return LLMModelsResponse(
        models=[LLMModelInfo(**m) for m in models_data],
        default_mode="auto",
    )


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
    if body.llm_selection:
        is_valid, err_msg, _ = validate_llm_selection(body.llm_selection, request.app.state)
        if not is_valid:
            raise HTTPException(status_code=400, detail=err_msg)

    request_id = str(uuid.uuid4())

    # Store the pending analysis request in app state
    pending = getattr(request.app.state, "pending_analyses", None)
    if pending is None:
        request.app.state.pending_analyses = {}
        pending = request.app.state.pending_analyses

    _hold(pending, request_id, {
        "body": body,
        "llm_selection": body.llm_selection.model_dump() if body.llm_selection else None,
        "additional_instructions": body.additional_instructions,
        "created_at": time.time(),
    })

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
    patient_context: str = Form(None),
    llm_selection: str = Form(None),
    additional_instructions: str = Form(None, max_length=2000),
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
            raw_data = json.loads(patient_context)
            context_data = PatientContextInput(**raw_data).model_dump()
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid patient_context JSON")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Parse optional llm_selection if provided (strict validation: reject invalid JSON or model)
    selection_data = None
    if llm_selection:
        try:
            raw_sel = json.loads(llm_selection)
            selection_input = LLMSelectionInput(**raw_sel)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid llm_selection JSON")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid llm_selection schema: {e}")

        is_valid, err_msg, _ = validate_llm_selection(selection_input, request.app.state)
        if not is_valid:
            raise HTTPException(status_code=400, detail=err_msg)
        selection_data = selection_input.model_dump()

    _hold(pending, request_id, {
        "type": "prescription_image",
        "image_bytes": file_bytes,
        "image_meta": validation_meta,
        "patient_context": context_data,
        "llm_selection": selection_data,
        "additional_instructions": additional_instructions,
        "created_at": time.time(),
    })

    log.info(f"POST /api/v1/analyze/prescription request_id={request_id} size={len(file_bytes)}")

    return {
        "request_id": request_id,
        "stream_url": f"/api/v1/stream/{request_id}",
        "validation": validation_meta
    }

from typing import Annotated, Literal, Optional

from pydantic import BaseModel, Field, StringConstraints


class ConfirmedMedicationItem(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    # Only reviewed states: an item still DETECTED or UNCERTAIN was never confirmed by the user.
    status: Literal["CONFIRMED", "EDITED", "USER_ADDED"]
    source: str = "VISION"
    raw_detected_name: Optional[str] = None

class ConfirmMedicationsRequest(BaseModel):
    confirmed_medications: list[ConfirmedMedicationItem] = Field(min_length=1)

@router.post(
    "/analyze/{request_id}/confirm",
    summary="Confirm medications for analysis",
)
async def confirm_medications(request_id: str, body: ConfirmMedicationsRequest, request: Request):
    """Accept the user's confirmation once, for a request that is waiting for it.

    The check and the update below run with no ``await`` between them, so on the single event loop
    that serves a request's stream and its confirmations no other confirmation can interleave: the
    first valid one is the decision, and it wakes the one waiting pipeline. An identical repeat is
    acknowledged and changes nothing; a different one is refused.
    """
    pending = getattr(request.app.state, "pending_analyses", {})
    analysis = pending.get(request_id)

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis request not found or expired")
    if analysis.get("finished"):
        raise HTTPException(status_code=409, detail="This analysis has already ended; upload the image again")
    if not analysis.get("awaiting_confirmation"):
        raise HTTPException(status_code=409, detail="This analysis is not waiting for a confirmation yet")
    accepted = analysis.get("confirmed_medications")
    if accepted is not None:
        if [m.model_dump() for m in accepted] == [m.model_dump() for m in body.confirmed_medications]:
            return {"status": "already_confirmed", "confirmed": accepted}
        raise HTTPException(status_code=409, detail="A different confirmation was already accepted for this analysis")

    analysis["confirmed_medications"] = body.confirmed_medications
    if "confirmation_event" in analysis:
        analysis["confirmation_event"].set()
    return {"status": "success", "confirmed": body.confirmed_medications}

@router.post(
    "/analyze/{request_id}/cancel",
    summary="Abandon an image analysis before its medications are confirmed",
)
async def cancel_analysis(request_id: str, request: Request):
    """End an image analysis the user abandoned; nothing of it is analysed.

    As in /confirm, the check and the update run with no ``await`` between them. A request whose
    stream is running is marked and its wait released, and that stream ends it with
    ``ANALYSIS_CANCELLED``. A request never streamed is dropped here, image included. A vision request
    in flight is closed and no fallback provider is tried; the provider may still have processed the
    image. Repeating a cancel is harmless.
    """
    pending = getattr(request.app.state, "pending_analyses", {})
    analysis = pending.get(request_id)

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis request not found or already ended")
    if analysis.get("cancelled"):
        return {"status": "cancelled"}
    if analysis.get("type") != "prescription_image":
        raise HTTPException(status_code=409, detail="Only an image analysis can be cancelled before confirmation")
    if analysis.get("finished") or analysis.get("confirmed_medications") is not None:
        raise HTTPException(status_code=409, detail="This analysis was already confirmed or has ended")

    analysis["cancelled"] = analysis["finished"] = True  # /confirm refuses it from now on
    if analysis.get("streaming"):
        if "confirmation_event" in analysis:
            analysis["confirmation_event"].set()
    else:
        pending.pop(request_id, None)
    return {"status": "cancelled"}

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

    expired = (analysis is not None and not analysis.get("streaming")
               and time.monotonic() > analysis.get("open_by", float("inf")))
    if expired:  # past its deadline before its timer ran (a busy loop): dropped, image included
        pending.pop(request_id, None)
        log.info("Request %s expired before its stream opened; dropped", request_id)
    if analysis is None or expired:
        async def error_stream():
            yield await _sse_event("error", {
                "code": "REQUEST_EXPIRED" if expired else "NOT_FOUND",
                "message": ("This analysis request expired before it started; nothing was analysed. "
                            "Submit it again." if expired else
                            f"Analysis {request_id} not found or expired."),
            })

        return StreamingResponse(error_stream(), media_type="text/event-stream")

    async def pipeline_stream():
        """Execute the analysis pipeline and emit SSE events."""
        # Its deadline timer may have dropped it after the check above; no await separates this
        # check from the mark below, so it cannot fire in between.
        if pending.get(request_id) is not analysis:
            yield await _sse_event("error", {
                "code": "REQUEST_EXPIRED",
                "message": "This analysis request expired before it started; nothing was analysed. Submit it again.",
            })
            return
        start_time = time.time()
        analysis["streaming"] = True  # from here a cancel is carried out by this stream

        try:
            from adaptive_trust_medical_rag.services.live_application import LiveMedicalRAGService
            service = LiveMedicalRAGService(request.app.state)

            # Support both direct_drugs and prescription_image
            drug_names = []
            patient_context_dict = None
            image_bytes = None
            image_meta = None
            additional_instructions = analysis.get("additional_instructions")

            if analysis.get("type") == "prescription_image":
                image_bytes = analysis.get("image_bytes")
                image_meta = analysis.get("image_meta")
                patient_context_dict = analysis.get("patient_context")
                # Create an event to wait for confirmation if not already present
                if "confirmation_event" not in analysis:
                    analysis["confirmation_event"] = asyncio.Event()
            else:
                body: AnalyzeRequest = analysis["body"]
                drug_names = body.drug_names
                patient_context_dict = body.patient_context.model_dump() if body.patient_context else None
                additional_instructions = (
                    body.additional_instructions
                    if hasattr(body, "additional_instructions")
                    else None
                )

            llm_selection_data = analysis.get("llm_selection")
            if not llm_selection_data and "body" in analysis:
                body_obj = analysis["body"]
                if getattr(body_obj, "llm_selection", None):
                    llm_selection_data = body_obj.llm_selection.model_dump()

            async for event_dict in service.execute(
                request_id=request_id,
                drug_names=drug_names,
                patient_context=patient_context_dict,
                start_time=start_time,
                image_bytes=image_bytes,
                image_meta=image_meta,
                analysis_state=analysis,
                llm_selection=llm_selection_data,
                additional_instructions=additional_instructions,
            ):
                yield await _sse_event(event_dict["event"], event_dict["data"])

        except asyncio.CancelledError:
            # The client dropped the stream (Starlette cancels it on http.disconnect): the request ends
            # as a cancel would, and the pipeline has already stopped its OCR or vision work.
            analysis["cancelled"] = analysis["finished"] = True
            log.info("Stream for %s closed by the client; the analysis was stopped", request_id)
            raise
        except Exception as e:
            log.error("Pipeline error for %s: %s", request_id, e)
            import traceback
            traceback.print_exc()
            yield await _sse_event("error", {
                "code": "PIPELINE_ERROR",
                "message": str(e),
            })
        finally:
            # Every exit ends the analysis (confirmation waits inside this stream), so the entry and
            # any uploaded image are dropped, and a second stream request cannot re-run the pipeline.
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
    from datetime import UTC, datetime
    return datetime.now(UTC).isoformat()


def _elapsed(start: float) -> float:
    """Milliseconds since start."""
    return round((time.time() - start) * 1000, 1)
