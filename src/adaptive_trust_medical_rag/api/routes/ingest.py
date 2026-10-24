"""POST /ingest route handler."""

from __future__ import annotations

import hashlib
import logging
import uuid

from fastapi import APIRouter, HTTPException, Request, status

from adaptive_trust_medical_rag.api.schemas import IngestRequest, IngestResponse

log = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Ingest a medical evidence document",
    tags=["ingest"],
)
async def post_ingest(body: IngestRequest, request: Request) -> IngestResponse:
    """
    Ingest a medical evidence document into the evidence store.

    - Computes SHA-256 content hash for poisoning detection.
    - Scores anomaly / poisoning risk before accepting the document.
    - Quarantines documents with high anomaly or poisoning scores.
    - Validates source tier and provenance metadata.

    **Security:** Source validation status must reach 'validated' before
    the document enters any retrieval index.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Compute content hash (poisoning detection anchor)
    content_bytes = body.content.encode("utf-8")
    content_hash = hashlib.sha256(content_bytes).hexdigest()

    log.info(
        "POST /ingest request_id=%s title=%s content_hash=%s",
        request_id,
        body.title[:50],
        content_hash,
    )

    # Resolve ingestion handler from app state (injected at startup)
    ingester = getattr(request.app.state, "ingester", None)
    if ingester is not None:
        try:
            result = ingester(body, content_hash)
            return result
        except Exception as exc:
            log.error("Ingestion error request_id=%s: %s", request_id, exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ingestion failed. Check quarantine logs.",
            ) from exc

    # No ingester: nothing was stored, scored or queued, so success must not be reported.
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="No ingester is configured; the document was not ingested.",
    )
