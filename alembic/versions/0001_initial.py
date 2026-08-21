"""Initial schema — evidence store for Adaptive Trust Medical RAG.

Creates all five core tables:
  - evidence_sources     : Authoritative source catalogue
  - documents            : Ingested evidence documents (SHA-256 hash)
  - evidence_chunks      : Chunked passages with 768-dim pgvector embeddings
  - evidence_provenance  : Immutable chunk-to-source provenance links
  - audit_events         : Append-only query/gate/answer audit log

Also enables the pgvector extension and creates performance indices.

Revision ID: 0001_initial
Revises: (none)
Create Date: 2026-08-21
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision: str = "0001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create full schema for Adaptive Trust Medical RAG evidence store."""

    # ── pgvector extension ───────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── Enum types ────────────────────────────────────────────────────────────
    source_tier_enum = postgresql.ENUM(
        "tier_1_regulatory",
        "tier_2_systematic",
        "tier_3_primary",
        "tier_4_clinical",
        "tier_5_grey",
        name="sourcetier",
        create_type=True,
    )
    source_validation_status_enum = postgresql.ENUM(
        "pending", "validated", "quarantined", "rejected",
        name="sourcevalidationstatus",
        create_type=True,
    )
    document_status_enum = postgresql.ENUM(
        "pending", "ingested", "chunked", "quarantined", "rejected",
        name="documentstatus",
        create_type=True,
    )
    risk_class_enum = postgresql.ENUM(
        "R0", "R1", "R2", "R3",
        name="riskclass",
        create_type=True,
    )
    gate_decision_enum = postgresql.ENUM(
        "release", "abstain", "warn",
        name="gatedecision",
        create_type=True,
    )

    # ── evidence_sources ──────────────────────────────────────────────────────
    op.create_table(
        "evidence_sources",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("doi", sa.String(256), nullable=True),
        sa.Column("pmid", sa.String(64), nullable=True),
        sa.Column(
            "source_tier",
            source_tier_enum,
            nullable=False,
            server_default="tier_5_grey",
        ),
        sa.Column(
            "validation_status",
            source_validation_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("authority_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("reputation_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("publication_year", sa.Integer(), nullable=True),
        sa.Column("is_open_access", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "extra_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("doi", name="uq_evidence_sources_doi"),
        sa.UniqueConstraint("pmid", name="uq_evidence_sources_pmid"),
    )
    op.create_index(
        "ix_evidence_sources_validation_status",
        "evidence_sources",
        ["validation_status"],
    )
    op.create_index(
        "ix_evidence_sources_source_tier",
        "evidence_sources",
        ["source_tier"],
    )

    # ── documents ─────────────────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evidence_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(1024), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),  # SHA-256 hex
        sa.Column(
            "status",
            document_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "ingestion_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("anomaly_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("poisoning_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("quarantine_reason", sa.Text(), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("content_hash", name="uq_documents_content_hash"),
    )
    op.create_index("ix_documents_source_id", "documents", ["source_id"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"])

    # ── evidence_chunks ───────────────────────────────────────────────────────
    op.create_table(
        "evidence_chunks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("token_count", sa.Integer(), nullable=True),
        # 768-dim dense embedding (sentence-transformers default)
        sa.Column(
            "embedding",
            sa.String(),  # placeholder; pgvector type set via raw SQL below
            nullable=True,
        ),
        sa.Column(
            "drug_entities",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "rxcui_entities",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("content_hash", sa.String(64), nullable=False),  # SHA-256
        sa.Column("bm25_tokens", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "document_id",
            "chunk_index",
            name="uq_evidence_chunks_doc_idx",
        ),
    )
    # Use vector(768) for the embedding column via raw ALTER
    op.execute(
        "ALTER TABLE evidence_chunks "
        "ALTER COLUMN embedding TYPE vector(768) "
        "USING NULL::vector(768)"
    )
    # IVFFlat index for ANN search (to be built after initial data load)
    op.execute(
        "CREATE INDEX ix_evidence_chunks_embedding_ivfflat "
        "ON evidence_chunks "
        "USING ivfflat (embedding vector_cosine_ops) "
        "WITH (lists = 100)"
    )
    op.create_index("ix_evidence_chunks_document_id", "evidence_chunks", ["document_id"])
    op.create_index("ix_evidence_chunks_content_hash", "evidence_chunks", ["content_hash"])

    # ── evidence_provenance ───────────────────────────────────────────────────
    op.create_table(
        "evidence_provenance",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evidence_chunks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evidence_sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content_hash", sa.String(64), nullable=False),   # SHA-256
        sa.Column("retrieval_method", sa.String(64), nullable=False),
        sa.Column(
            "retrieval_score",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
        sa.Column(
            "trust_score",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
        sa.Column(
            "validation_status",
            source_validation_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "retrieved_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_evidence_provenance_chunk_id", "evidence_provenance", ["chunk_id"])
    op.create_index("ix_evidence_provenance_source_id", "evidence_provenance", ["source_id"])
    op.create_index(
        "ix_evidence_provenance_trust_score", "evidence_provenance", ["trust_score"]
    )

    # ── audit_events ──────────────────────────────────────────────────────────
    op.create_table(
        "audit_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("session_id", sa.String(64), nullable=False),
        # Privacy: query_hash only — never raw query text
        sa.Column("query_hash", sa.String(64), nullable=False),
        sa.Column(
            "risk_class",
            risk_class_enum,
            nullable=False,
            server_default="R1",
        ),
        sa.Column(
            "gate_decision",
            gate_decision_enum,
            nullable=False,
            server_default="abstain",
        ),
        sa.Column("trust_score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "retrieved_chunk_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "drug_entities",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        # answer_hash: SHA-256 of the generated answer (never raw answer)
        sa.Column("answer_hash", sa.String(64), nullable=True),
        sa.Column(
            "extra_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_audit_events_session_id", "audit_events", ["session_id"])
    op.create_index("ix_audit_events_query_hash", "audit_events", ["query_hash"])
    op.create_index("ix_audit_events_risk_class", "audit_events", ["risk_class"])
    op.create_index("ix_audit_events_gate_decision", "audit_events", ["gate_decision"])
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])


def downgrade() -> None:
    """Drop all tables and enums in reverse dependency order."""
    op.drop_table("audit_events")
    op.drop_table("evidence_provenance")
    op.drop_table("evidence_chunks")
    op.drop_table("documents")
    op.drop_table("evidence_sources")

    # Drop enum types
    for enum_name in [
        "gatedecision",
        "riskclass",
        "documentstatus",
        "sourcevalidationstatus",
        "sourcetier",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")

    op.execute("DROP EXTENSION IF EXISTS vector")
