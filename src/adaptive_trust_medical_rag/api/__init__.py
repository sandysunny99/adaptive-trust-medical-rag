"""FastAPI HTTP layer for Adaptive Trust Medical RAG."""

from adaptive_trust_medical_rag.api.app import create_app
from adaptive_trust_medical_rag.api.schemas import (
    AuditEventItem,
    AuditResponse,
    CitationItem,
    ErrorResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    QueryRequest,
    QueryResponse,
)

__all__ = [
    "create_app",
    "AuditEventItem",
    "AuditResponse",
    "CitationItem",
    "ErrorResponse",
    "HealthResponse",
    "IngestRequest",
    "IngestResponse",
    "QueryRequest",
    "QueryResponse",
]
