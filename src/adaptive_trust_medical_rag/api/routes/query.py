"""POST /query route handler."""

from __future__ import annotations

import logging
import uuid
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException, Request, status

from adaptive_trust_medical_rag.api.schemas import (
    CitationItem,
    QueryRequest,
    QueryResponse,
)
from adaptive_trust_medical_rag.orchestrator.rag_orchestrator import (
    PipelineStatus,
    RAGRequest,
    RAGResponse,
)

log = logging.getLogger(__name__)
router = APIRouter()


def _get_pipeline(request: Request) -> Callable:
    """FastAPI dependency: resolve pipeline callable from app state."""
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Pipeline not initialised.",
        )
    return pipeline


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Submit a pharmacological research query",
    tags=["query"],
)
async def post_query(
    body: QueryRequest,
    request: Request,
    pipeline: Callable = Depends(_get_pipeline),
) -> QueryResponse:
    """
    Process a pharmacological research query through the full RAG pipeline.

    - Sanitizes the input query (injection detection, PHI scrubbing).
    - Classifies risk tier (R0-R3) automatically unless overridden.
    - Runs hybrid retrieval -> trust scoring -> dual-gate verification.
    - Returns a grounded answer with citations or a structured abstention.

    **Privacy:** Query hash (SHA-256) is logged, never raw query text.
    **Disclaimer:** Research output only. Not for clinical use.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    session_id = body.session_id or str(uuid.uuid4())

    log.info(
        "POST /query request_id=%s session=%s risk_override=%s",
        request_id,
        session_id,
        body.risk_tier_override,
    )

    rag_request = RAGRequest(
        query=body.query,
        session_id=session_id,
        risk_tier_override=body.risk_tier_override,
    )

    try:
        rag_response: RAGResponse = pipeline(rag_request)
    except Exception as exc:
        log.error("Pipeline error request_id=%s: %s", request_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Pipeline execution error. Please retry.",
        ) from exc

    # Build citations from retrieved chunk IDs + trust scores
    citations = [
        CitationItem(
            chunk_id=cid,
            source_name=f"Source {i + 1}",
            trust_score=rag_response.trust_scores[i]
            if i < len(rag_response.trust_scores)
            else 0.0,
            retrieval_method="hybrid-rrk",
        )
        for i, cid in enumerate(rag_response.retrieved_chunk_ids)
    ]

    # Build abstention reason if pipeline abstained
    abstention_reason: str | None = None
    if rag_response.status == PipelineStatus.abstained:
        vr = rag_response.verification_report
        abstention_reason = vr.explanation if vr else "Insufficient evidence."

    return QueryResponse(
        session_id=rag_response.session_id,
        query_hash=rag_response.query_hash,
        risk_tier=rag_response.risk_tier,
        status=rag_response.status.value,
        answer=rag_response.answer,
        confidence=rag_response.confidence,
        citations=citations,
        gate_decision=rag_response.gate_decision,
        abstention_reason=abstention_reason,
    )
