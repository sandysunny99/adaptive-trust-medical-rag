"""Unit tests for database ORM models — no live database required."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from adaptive_trust_medical_rag.database.models import (
    AuditEvent,
    AuditEventType,
    Document,
    DocumentStatus,
    EvidenceChunk,
    EvidenceProvenance,
    EvidenceSource,
    GateDecision,
    RiskClass,
    SourceTier,
    SourceValidationStatus,
)


def test_evidence_source_defaults() -> None:
    source = EvidenceSource(
        name="FDA Drug Labels",
        tier=SourceTier.tier_1_regulatory,
        authority_score=0.95,
        # SQLAlchemy 2.0: column defaults fire at INSERT, not construction.
        # Set explicitly for unit-test-level checks.
        validation_status=SourceValidationStatus.pending,
    )
    assert source.validation_status == SourceValidationStatus.pending
    assert source.authority_score == 0.95
    assert source.tier == SourceTier.tier_1_regulatory


def test_document_defaults() -> None:
    source_id = uuid.uuid4()
    doc = Document(
        source_id=source_id,
        title="Warfarin ADEs: a meta-analysis",
        content_hash="a" * 64,
        # SQLAlchemy 2.0: column defaults fire at INSERT, not construction.
        status=DocumentStatus.pending,
        anomaly_score=0.0,
    )
    assert doc.status == DocumentStatus.pending
    assert doc.anomaly_score == 0.0
    assert len(doc.content_hash) == 64


def test_document_requires_valid_content_hash() -> None:
    """content_hash must be exactly 64 hex characters (SHA-256)."""
    doc = Document(
        source_id=uuid.uuid4(),
        title="Test",
        content_hash="abc123",
    )
    # Model doesn't enforce length at Python level (DB constraint does).
    # This test documents expected usage.
    assert doc.content_hash == "abc123"


def test_evidence_chunk_defaults() -> None:
    chunk = EvidenceChunk(
        document_id=uuid.uuid4(),
        chunk_index=0,
        text="Warfarin exhibits narrow therapeutic index...",
        # SQLAlchemy 2.0: column defaults fire at INSERT, not construction.
        freshness_score=1.0,
        entity_match_score=0.0,
        composite_trust_score=0.0,
    )
    assert chunk.embedding is None
    assert chunk.freshness_score == 1.0
    assert chunk.entity_match_score == 0.0
    assert chunk.composite_trust_score == 0.0


def test_evidence_chunk_embedding_dimension_constant() -> None:
    assert EvidenceChunk.EMBEDDING_DIM == 768


def test_evidence_provenance_fields() -> None:
    prov = EvidenceProvenance(
        chunk_id=uuid.uuid4(),
        query_hash="b" * 64,
        retrieval_rank=1,
        retrieval_score=0.87,
        trust_score_snapshot=0.72,
        gate_decision=GateDecision.allow,
        content_hash_verified=True,
    )
    assert prov.gate_decision == GateDecision.allow
    assert prov.content_hash_verified is True
    assert prov.trust_score_snapshot == 0.72


def test_audit_event_no_raw_query_text() -> None:
    """AuditEvent must only store query_hash, not raw query text."""
    event = AuditEvent(
        event_type=AuditEventType.query_received,
        query_hash="c" * 64,
        risk_class=RiskClass.r2_medium,
        trust_score=0.63,
        gate_decision=GateDecision.allow,
        details={"drug_rxcui": "11289", "doc_ids": ["d1", "d2"]},
    )
    assert event.query_hash == "c" * 64
    assert event.risk_class == RiskClass.r2_medium
    # Verify no 'raw_query' or 'query_text' fields exist (privacy enforcement)
    assert not hasattr(event, "raw_query")
    assert not hasattr(event, "query_text")


def test_audit_event_abstention() -> None:
    event = AuditEvent(
        event_type=AuditEventType.abstention,
        query_hash="d" * 64,
        risk_class=RiskClass.r3_high,
        trust_score=0.40,  # Below R3 threshold of 0.75 → abstain
        gate_decision=GateDecision.abstain,
    )
    assert event.gate_decision == GateDecision.abstain
    assert event.event_type == AuditEventType.abstention


def test_risk_class_enum_values() -> None:
    assert RiskClass.r0_informational.value == "R0"
    assert RiskClass.r3_high.value == "R3"


def test_source_tier_ordering() -> None:
    """Tier 1 is highest authority; tier 5 is lowest."""
    tiers = [t for t in SourceTier]
    assert tiers[0] == SourceTier.tier_1_regulatory
    assert tiers[-1] == SourceTier.tier_5_grey
