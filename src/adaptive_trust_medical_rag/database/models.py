"""SQLAlchemy 2.0 async ORM models for the Medical RAG evidence store.

Tables:
    evidence_sources    — Authoritative source catalogue with reputation scoring
    documents           — Ingested evidence documents with SHA-256 content hashes
    evidence_chunks     — Chunked document passages with 768-dim dense embeddings
    evidence_provenance — Immutable provenance records linking chunks to sources
    audit_events        — Append-only audit log for every query, gate decision, and answer

Privacy & Security Rules (AGENTS.md / privacy.md):
    - No PHI/PII is stored in any column.
    - Raw query text is NEVER stored; only query_hash (SHA-256 hex).
    - Document content_hash enforces retrieval poisoning detection.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class Base(DeclarativeBase):
    """Common base for all ORM models."""


# ─────────────────────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────────────────────


class SourceTier(str, PyEnum):
    """Authority tier from medical-source-validation skill."""

    tier_1_regulatory = "tier_1_regulatory"  # FDA, EMA, WHO
    tier_2_systematic = "tier_2_systematic"  # Cochrane, meta-analyses
    tier_3_primary = "tier_3_primary"  # Peer-reviewed RCTs
    tier_4_clinical = "tier_4_clinical"  # Clinical guidelines
    tier_5_grey = "tier_5_grey"  # Grey literature, preprints


class SourceValidationStatus(str, PyEnum):
    pending = "pending"
    validated = "validated"
    quarantined = "quarantined"
    rejected = "rejected"


class DocumentStatus(str, PyEnum):
    pending = "pending"
    ingested = "ingested"
    chunked = "chunked"
    quarantined = "quarantined"
    rejected = "rejected"


class RiskClass(str, PyEnum):
    r0_informational = "R0"
    r1_low = "R1"
    r2_medium = "R2"
    r3_high = "R3"


class GateDecision(str, PyEnum):
    allow = "allow"
    abstain = "abstain"
    reject = "reject"


class AuditEventType(str, PyEnum):
    query_received = "query_received"
    risk_classified = "risk_classified"
    retrieval_complete = "retrieval_complete"
    evidence_gate_pass = "evidence_gate_pass"
    evidence_gate_fail = "evidence_gate_fail"
    answer_generated = "answer_generated"
    answer_gate_pass = "answer_gate_pass"
    answer_gate_fail = "answer_gate_fail"
    abstention = "abstention"
    injection_detected = "injection_detected"
    poisoning_detected = "poisoning_detected"


# ─────────────────────────────────────────────────────────────────────────────
# Table: evidence_sources
# ─────────────────────────────────────────────────────────────────────────────


class EvidenceSource(Base):
    """Catalogue of authoritative evidence sources with authority scoring."""

    __tablename__ = "evidence_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    tier: Mapped[SourceTier] = mapped_column(
        Enum(SourceTier, name="source_tier"), nullable=False
    )
    authority_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="Normalised 0.0–1.0 authority score"
    )
    validation_status: Mapped[SourceValidationStatus] = mapped_column(
        Enum(SourceValidationStatus, name="source_validation_status"),
        nullable=False,
        default=SourceValidationStatus.pending,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )

    documents: Mapped[list[Document]] = relationship(back_populates="source")

    __table_args__ = (
        Index("ix_evidence_sources_tier", "tier"),
        Index("ix_evidence_sources_validation_status", "validation_status"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Table: documents
# ─────────────────────────────────────────────────────────────────────────────


class Document(Base):
    """Ingested evidence document with immutable SHA-256 content hash."""

    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence_sources.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(1024), nullable=False)
    doi: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pmid: Mapped[str | None] = mapped_column(String(64), nullable=True)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="SHA-256 hex digest of raw document content (poisoning detection)",
    )
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, name="document_status"),
        nullable=False,
        default=DocumentStatus.pending,
    )
    anomaly_score: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0, comment="0.0 = clean, 1.0 = highly anomalous"
    )
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    source: Mapped[EvidenceSource] = relationship(back_populates="documents")
    chunks: Mapped[list[EvidenceChunk]] = relationship(back_populates="document")

    __table_args__ = (
        Index("ix_documents_source_id", "source_id"),
        Index("ix_documents_status", "status"),
        Index("ix_documents_content_hash", "content_hash"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Table: evidence_chunks
# ─────────────────────────────────────────────────────────────────────────────


class EvidenceChunk(Base):
    """Chunked document passage with dense embedding for vector retrieval."""

    __tablename__ = "evidence_chunks"

    EMBEDDING_DIM = 768  # Sentence-transformer embedding dimension (Phase 10)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(EMBEDDING_DIM), nullable=True, comment="Dense 768-dim sentence embedding"
    )
    # Drug entity normalization fields (Phase 6)
    drug_rxcui: Mapped[str | None] = mapped_column(String(64), nullable=True)
    drug_generic_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # Trust scoring fields
    freshness_score: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    entity_match_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    composite_trust_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    document: Mapped[Document] = relationship(back_populates="chunks")
    provenance: Mapped[list[EvidenceProvenance]] = relationship(back_populates="chunk")

    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="uq_chunk_doc_idx"),
        Index("ix_evidence_chunks_document_id", "document_id"),
        Index("ix_evidence_chunks_drug_rxcui", "drug_rxcui"),
        # HNSW vector index created by Alembic migration (Phase 5)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Table: evidence_provenance
# ─────────────────────────────────────────────────────────────────────────────


class EvidenceProvenance(Base):
    """Immutable provenance record linking retrieved chunks to query sessions."""

    __tablename__ = "evidence_provenance"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence_chunks.id", ondelete="RESTRICT"), nullable=False
    )
    query_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="SHA-256 hash of normalized query — no raw query text stored",
    )
    retrieval_rank: Mapped[int] = mapped_column(Integer, nullable=False)
    retrieval_score: Mapped[float] = mapped_column(Float, nullable=False)
    trust_score_snapshot: Mapped[float] = mapped_column(Float, nullable=False)
    gate_decision: Mapped[GateDecision] = mapped_column(
        Enum(GateDecision, name="gate_decision"), nullable=False
    )
    content_hash_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    chunk: Mapped[EvidenceChunk] = relationship(back_populates="provenance")

    __table_args__ = (
        Index("ix_evidence_provenance_query_hash", "query_hash"),
        Index("ix_evidence_provenance_chunk_id", "chunk_id"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Table: audit_events
# ─────────────────────────────────────────────────────────────────────────────


class AuditEvent(Base):
    """Append-only audit trail — no raw PII or PHI stored anywhere in this table.

    Per privacy.md:
        - Only query_hash (SHA-256), normalized entity CUIs, document IDs,
          trust scores, and model metadata are stored.
        - Raw query text is NEVER stored.
    """

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[AuditEventType] = mapped_column(
        Enum(AuditEventType, name="audit_event_type"), nullable=False
    )
    query_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    risk_class: Mapped[RiskClass | None] = mapped_column(
        Enum(RiskClass, name="risk_class"), nullable=True
    )
    trust_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    gate_decision: Mapped[GateDecision | None] = mapped_column(
        Enum(GateDecision, name="gate_decision_audit"),
        nullable=True,
    )
    model_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    config_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Entity CUIs, document IDs, gate metadata — no PHI"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )

    __table_args__ = (
        Index("ix_audit_events_event_type", "event_type"),
        Index("ix_audit_events_query_hash", "query_hash"),
        Index("ix_audit_events_created_at", "created_at"),
        Index("ix_audit_events_session_id", "session_id"),
    )
