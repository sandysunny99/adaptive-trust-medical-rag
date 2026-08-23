"""GET /audit/{session_id} route handler."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request, status

from adaptive_trust_medical_rag.api.schemas import AuditEventItem, AuditResponse

log = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/audit/{session_id}",
    response_model=AuditResponse,
    summary="Retrieve audit log for a session",
    tags=["audit"],
)
async def get_audit(session_id: str, request: Request) -> AuditResponse:
    """
    Return the audit event log for a given session ID.

    **Privacy:** Events contain only query_hash (SHA-256), not raw queries.
    **Security:** Callers must supply a valid session_id they own.

    Returns an empty events list if no events are found for the session.
    """
    if len(session_id) < 8 or len(session_id) > 64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id must be 8-64 characters.",
        )

    audit_store = getattr(request.app.state, "audit_store", None)
    if audit_store is not None:
        try:
            events = await audit_store.get_events(session_id)
        except Exception as exc:
            log.error("Audit retrieval error session=%s: %s", session_id, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve audit log.",
            ) from exc
        items = [AuditEventItem(**e) for e in events]
    else:
        # No live DB: return empty (dev/test mode)
        items = []

    return AuditResponse(
        session_id=session_id,
        event_count=len(items),
        events=items,
    )
