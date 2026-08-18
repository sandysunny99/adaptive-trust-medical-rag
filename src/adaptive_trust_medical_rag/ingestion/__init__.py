"""Ingestion package for adaptive-trust-medical-rag."""

from adaptive_trust_medical_rag.ingestion.evidence_ingestion import (
    EvidenceChunkData,
    EvidenceIngestionPipeline,
    IngestionResult,
    IngestionSourceType,
    IngestionStatus,
    PoisoningReport,
    ProvenanceRecord,
    RawDocument,
    chunk_document,
    compute_sha256,
    inspect_for_poisoning,
)

__all__ = [
    "EvidenceChunkData",
    "EvidenceIngestionPipeline",
    "IngestionResult",
    "IngestionSourceType",
    "IngestionStatus",
    "PoisoningReport",
    "ProvenanceRecord",
    "RawDocument",
    "chunk_document",
    "compute_sha256",
    "inspect_for_poisoning",
]
