"""Pydantic request/response models for the Medical RAG HTTP API.

Privacy rules enforced at schema level:
  - QueryRequest.query is sanitized before pipeline entry.
  - No PHI fields accepted or returned.
  - Session IDs are opaque UUIDs; raw query text is never logged.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """POST /query request body."""

    query: str = Field(
        ...,
        min_length=3,
        max_length=2048,
        description="Pharmacological research query (no PHI).",
    )
    session_id: str | None = Field(
        default=None,
        description="Optional opaque session UUID for audit correlation.",
    )
    risk_tier_override: str | None = Field(
        default=None,
        pattern=r"^R[0-3]$",
        description="Force a specific risk tier (R0-R3). If None, auto-classified.",
    )

    @field_validator("query")
    @classmethod
    def query_no_phi_hint(cls, v: str) -> str:
        """Basic check: reject queries that look like they contain PHI patterns."""
        import re

        phi_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",   # SSN
            r"\bMRN\s*#?\s*\d+\b",       # MRN
            r"\bDOB:\s*\d",              # Date of birth marker
        ]
        for pat in phi_patterns:
            if re.search(pat, v, re.IGNORECASE):
                raise ValueError(
                    "Query appears to contain Protected Health Information (PHI). "
                    "This system processes only de-identified research queries."
                )
        return v


class CitationItem(BaseModel):
    """Single evidence citation in a query response."""

    chunk_id: str
    source_name: str
    trust_score: float
    retrieval_method: str


class QueryResponse(BaseModel):
    """POST /query response body."""

    session_id: str
    query_hash: str = Field(description="SHA-256 of the query (never raw text).")
    risk_tier: str
    status: str = Field(description="released | abstained | error")
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    citations: list[CitationItem] = Field(default_factory=list)
    gate_decision: str
    abstention_reason: str | None = None
    disclaimer: str = (
        "RESEARCH OUTPUT ONLY. Not reviewed by clinicians. "
        "Not for clinical use. Evidence-grounded response from a research testbed."
    )


class IngestRequest(BaseModel):
    """POST /ingest request body."""

    title: str = Field(..., min_length=3, max_length=1024)
    content: str = Field(..., min_length=10, max_length=500_000)
    source_url: str | None = Field(default=None, max_length=2048)
    doi: str | None = Field(default=None, max_length=256)
    pmid: str | None = Field(default=None, max_length=64)
    publication_year: int | None = Field(default=None, ge=1900, le=2100)
    source_tier: str = Field(
        default="tier_5_grey",
        pattern=r"^tier_[1-5]_(regulatory|systematic|primary|clinical|grey)$",
    )


class IngestResponse(BaseModel):
    """POST /ingest response body."""

    document_id: str
    content_hash: str
    chunk_count: int
    status: str
    anomaly_score: float
    poisoning_score: float
    quarantined: bool
    message: str


class HealthResponse(BaseModel):
    """GET /health response body."""

    status: str = Field(description="ok | degraded | unhealthy")
    database: bool
    pgvector: bool
    version: str
    uptime_seconds: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class AuditEventItem(BaseModel):
    """Single audit event record."""

    event_id: str
    session_id: str
    query_hash: str
    risk_class: str
    gate_decision: str
    trust_score: float | None
    confidence: float | None
    created_at: str


class AuditResponse(BaseModel):
    """GET /audit/{session_id} response body."""

    session_id: str
    event_count: int
    events: list[AuditEventItem]


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    error: str
    detail: str | None = None
    request_id: str | None = None
