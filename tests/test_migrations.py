"""
Tests for Phase 18 - Alembic Database Migrations.

Tests run without a live database:
  - Migration file structure and metadata
  - Chain integrity (no gaps, no cycles)
  - All expected tables present in upgrade()
  - All expected indexes defined
  - Privacy constraints (no raw query/answer text columns)
  - Downgrade covers all tables from upgrade
  - migration_utils helpers
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from adaptive_trust_medical_rag.database.migration_utils import (
    get_migration_chain,
    list_migration_versions,
    verify_migration_chain,
)

VERSIONS_DIR = Path("alembic/versions")
INITIAL_MIGRATION = VERSIONS_DIR / "0001_initial.py"


def _migration_text() -> str:
    return INITIAL_MIGRATION.read_text(encoding="utf-8")


def _tables_in_upgrade(text: str) -> list[str]:
    return re.findall(r'op\.create_table\(\s*["\']([^"\']+)["\']', text)


def _indexes_in_upgrade(text: str) -> list[str]:
    return re.findall(r'op\.create_index\(\s*["\']([^"\']+)["\']', text)


def _columns_in_table(text: str, table: str) -> list[str]:
    """Extract column names from a create_table block."""
    block = re.search(rf'create_table\(\s*["\'{table}"\']', text)
    if not block:
        return []
    return re.findall(
        r'sa\.Column\(\s*["\']([^"\']+)["\']', text[block.start() : block.start() + 3000]
    )


class TestMigrationFile:
    def test_initial_migration_exists(self) -> None:
        assert INITIAL_MIGRATION.exists(), "0001_initial.py migration file missing"

    def test_revision_id_correct(self) -> None:
        text = _migration_text()
        assert 'revision: str = "0001_initial"' in text

    def test_down_revision_is_none(self) -> None:
        text = _migration_text()
        assert "down_revision" in text
        m = re.search(r"down_revision.*=\s*(.+)$", text, re.MULTILINE)
        assert m, "down_revision not found"
        assert "None" in m.group(1)

    def test_upgrade_function_exists(self) -> None:
        text = _migration_text()
        assert "def upgrade() -> None:" in text

    def test_downgrade_function_exists(self) -> None:
        text = _migration_text()
        assert "def downgrade() -> None:" in text

    def test_file_is_valid_python(self) -> None:
        text = _migration_text()
        ast.parse(text)  # raises SyntaxError on bad Python

    def test_no_raw_api_keys_in_file(self) -> None:
        text = _migration_text()
        # No obvious credential patterns
        assert "password=" not in text.lower()
        assert "secret_key" not in text.lower()


class TestTablesCreated:
    """Verify all 5 core tables are created in upgrade()."""

    EXPECTED_TABLES = {
        "evidence_sources",
        "documents",
        "evidence_chunks",
        "evidence_provenance",
        "audit_events",
    }

    def test_all_tables_created(self) -> None:
        text = _migration_text()
        tables = set(_tables_in_upgrade(text))
        assert self.EXPECTED_TABLES == tables, (
            f"Missing: {self.EXPECTED_TABLES - tables}, Extra: {tables - self.EXPECTED_TABLES}"
        )

    def test_evidence_sources_created(self) -> None:
        assert "evidence_sources" in _tables_in_upgrade(_migration_text())

    def test_documents_created(self) -> None:
        assert "documents" in _tables_in_upgrade(_migration_text())

    def test_evidence_chunks_created(self) -> None:
        assert "evidence_chunks" in _tables_in_upgrade(_migration_text())

    def test_evidence_provenance_created(self) -> None:
        assert "evidence_provenance" in _tables_in_upgrade(_migration_text())

    def test_audit_events_created(self) -> None:
        assert "audit_events" in _tables_in_upgrade(_migration_text())

    def test_pgvector_extension_enabled(self) -> None:
        assert "CREATE EXTENSION IF NOT EXISTS vector" in _migration_text()

    def test_vector_768_dim_set(self) -> None:
        assert "vector(768)" in _migration_text()

    def test_ivfflat_index_created(self) -> None:
        assert "ivfflat" in _migration_text()


class TestColumnsAndConstraints:
    def test_audit_events_has_query_hash(self) -> None:
        text = _migration_text()
        # query_hash present in audit_events (privacy: not raw query)
        assert '"query_hash"' in text or "'query_hash'" in text

    def test_audit_events_no_raw_query_column(self) -> None:
        text = _migration_text()
        # Must NOT have a 'query' column (only query_hash)
        audit_block_start = text.find('"audit_events"')
        if audit_block_start == -1:
            audit_block_start = text.find("'audit_events'")
        audit_block = text[audit_block_start : audit_block_start + 2000]
        cols = re.findall(r'sa\.Column\(\s*["\']([^"\']+)["\']', audit_block)
        assert "query" not in cols, "audit_events must not store raw query text"

    def test_documents_has_content_hash(self) -> None:
        text = _migration_text()
        assert "content_hash" in text

    def test_evidence_sources_has_unique_doi(self) -> None:
        text = _migration_text()
        assert "uq_evidence_sources_doi" in text

    def test_evidence_sources_has_unique_pmid(self) -> None:
        text = _migration_text()
        assert "uq_evidence_sources_pmid" in text

    def test_documents_has_unique_content_hash(self) -> None:
        text = _migration_text()
        assert "uq_documents_content_hash" in text

    def test_evidence_chunks_has_unique_doc_chunk_idx(self) -> None:
        text = _migration_text()
        assert "uq_evidence_chunks_doc_idx" in text

    def test_all_tables_have_uuid_pk(self) -> None:
        text = _migration_text()
        assert "gen_random_uuid()" in text

    def test_audit_events_has_answer_hash_not_answer(self) -> None:
        text = _migration_text()
        assert "answer_hash" in text
        # raw answer text must not be stored
        audit_block_start = text.find('"audit_events"')
        if audit_block_start == -1:
            audit_block_start = text.find("'audit_events'")
        audit_block = text[audit_block_start : audit_block_start + 2000]
        cols = re.findall(r'sa\.Column\(\s*["\']([^"\']+)["\']', audit_block)
        assert "answer" not in cols, "Must not store raw answer text"

    def test_risk_class_enum_defined(self) -> None:
        text = _migration_text()
        assert "riskclass" in text or "risk_class" in text

    def test_gate_decision_enum_defined(self) -> None:
        text = _migration_text()
        assert "gatedecision" in text or "gate_decision" in text


class TestIndexes:
    EXPECTED_INDEXES = [
        "ix_evidence_sources_validation_status",
        "ix_evidence_sources_source_tier",
        "ix_documents_source_id",
        "ix_documents_status",
        "ix_documents_content_hash",
        "ix_evidence_chunks_document_id",
        "ix_evidence_chunks_content_hash",
        "ix_evidence_provenance_chunk_id",
        "ix_evidence_provenance_source_id",
        "ix_evidence_provenance_trust_score",
        "ix_audit_events_session_id",
        "ix_audit_events_query_hash",
        "ix_audit_events_risk_class",
        "ix_audit_events_gate_decision",
        "ix_audit_events_created_at",
    ]

    def test_all_expected_indexes_present(self) -> None:
        text = _migration_text()
        indexes = _indexes_in_upgrade(text)
        for expected in self.EXPECTED_INDEXES:
            assert expected in indexes, f"Missing index: {expected}"

    def test_audit_events_query_hash_indexed(self) -> None:
        assert "ix_audit_events_query_hash" in _indexes_in_upgrade(_migration_text())

    def test_trust_score_indexed(self) -> None:
        assert "ix_evidence_provenance_trust_score" in _indexes_in_upgrade(_migration_text())


class TestDowngrade:
    def test_downgrade_drops_audit_events(self) -> None:
        text = _migration_text()
        down_start = text.find("def downgrade()")
        downgrade_block = text[down_start:]
        assert "audit_events" in downgrade_block

    def test_downgrade_drops_evidence_provenance(self) -> None:
        text = _migration_text()
        down_start = text.find("def downgrade()")
        assert "evidence_provenance" in text[down_start:]

    def test_downgrade_drops_evidence_chunks(self) -> None:
        text = _migration_text()
        assert "evidence_chunks" in text[text.find("def downgrade()") :]

    def test_downgrade_drops_documents(self) -> None:
        text = _migration_text()
        assert "documents" in text[text.find("def downgrade()") :]

    def test_downgrade_drops_evidence_sources(self) -> None:
        text = _migration_text()
        assert "evidence_sources" in text[text.find("def downgrade()") :]

    def test_downgrade_drops_enums(self) -> None:
        text = _migration_text()
        down_block = text[text.find("def downgrade()") :]
        assert "DROP TYPE" in down_block

    def test_downgrade_drops_vector_extension(self) -> None:
        text = _migration_text()
        assert "DROP EXTENSION" in text[text.find("def downgrade()") :]


class TestMigrationUtils:
    def test_list_versions_returns_list(self) -> None:
        versions = list_migration_versions()
        assert isinstance(versions, list)

    def test_initial_migration_listed(self) -> None:
        versions = list_migration_versions()
        revisions = [v["revision"] for v in versions]
        assert "0001_initial" in revisions

    def test_initial_migration_has_5_tables(self) -> None:
        versions = list_migration_versions()
        v0 = next(v for v in versions if v["revision"] == "0001_initial")
        assert len(v0["tables_created"]) == 5

    def test_get_migration_chain_starts_with_initial(self) -> None:
        chain = get_migration_chain()
        assert len(chain) >= 1
        assert chain[0] == "0001_initial"

    def test_verify_migration_chain_no_errors(self) -> None:
        errors = verify_migration_chain()
        assert errors == [], f"Chain errors: {errors}"

    def test_version_has_filename(self) -> None:
        versions = list_migration_versions()
        for v in versions:
            assert "filename" in v
            assert v["filename"].endswith(".py")
