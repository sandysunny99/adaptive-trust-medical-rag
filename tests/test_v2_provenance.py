"""
Tests for provenance propagation in the evidence corpus loader.
Verifies that V2 provenance repair is correct and that the security policy remains intact.
"""
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from adaptive_trust_medical_rag.evaluation.live_variants import load_evidence_corpus
from adaptive_trust_medical_rag.security_extensions.poisoning_detector import (
    RetrievalPoisoningDetector,
)
from adaptive_trust_medical_rag.security.security_context import SecurityState
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate


class TestProvenancePropagation:
    """Tests for V2 provenance repair: load_evidence_corpus must populate provenance."""

    def test_all_candidates_have_provenance_key(self):
        """Candidate.metadata['provenance'] must exist for every loaded document."""
        corpus = load_evidence_corpus()
        for c in corpus:
            assert "provenance" in c.metadata, (
                f"{c.chunk_id}: metadata missing 'provenance' key"
            )

    def test_provenance_is_non_empty_dict(self):
        """Provenance must be a non-empty dict (falsy {} triggers BLOCK)."""
        corpus = load_evidence_corpus()
        for c in corpus:
            prov = c.metadata["provenance"]
            assert isinstance(prov, dict), f"{c.chunk_id}: provenance is not a dict"
            assert len(prov) > 0, f"{c.chunk_id}: provenance is empty"

    def test_provenance_has_required_fields(self):
        """Provenance must contain the fields specified by the ingestion skill contract."""
        required = {"source", "document_id", "content_hash", "source_authority", "validation_status"}
        corpus = load_evidence_corpus()
        for c in corpus:
            prov = c.metadata["provenance"]
            missing = required - set(prov.keys())
            assert not missing, (
                f"{c.chunk_id}: provenance missing fields: {missing}"
            )

    def test_provenance_source_populated(self):
        """Provenance source must be a non-empty string."""
        corpus = load_evidence_corpus()
        for c in corpus:
            source = c.metadata["provenance"]["source"]
            assert isinstance(source, str) and len(source) > 0, (
                f"{c.chunk_id}: provenance source is empty"
            )

    def test_provenance_document_id_matches(self):
        """Provenance document_id must match the candidate's document_id."""
        corpus = load_evidence_corpus()
        for c in corpus:
            assert c.metadata["provenance"]["document_id"] == c.document_id, (
                f"{c.chunk_id}: provenance document_id mismatch"
            )

    def test_provenance_content_hash_is_valid_sha256(self):
        """Content hash must be a valid SHA-256 hex digest of the document text."""
        corpus = load_evidence_corpus()
        for c in corpus:
            expected = hashlib.sha256(c.text.encode("utf-8")).hexdigest()
            assert c.metadata["provenance"]["content_hash"] == expected, (
                f"{c.chunk_id}: content hash mismatch"
            )

    def test_provenance_validation_status(self):
        """All corpus documents must have validation_status='validated'."""
        corpus = load_evidence_corpus()
        for c in corpus:
            assert c.metadata["provenance"]["validation_status"] == "validated", (
                f"{c.chunk_id}: validation_status is not 'validated'"
            )


class TestProvenanceSecurityPolicy:
    """Tests that the MISSING_PROVENANCE → BLOCK policy remains intact."""

    def setup_method(self):
        self.detector = RetrievalPoisoningDetector()

    def test_valid_provenance_allows(self):
        """Non-empty provenance with safe source → ALLOW."""
        corpus = load_evidence_corpus()
        for c in corpus:
            prov = c.metadata["provenance"]
            result = self.detector.inspect_provenance(prov, c.chunk_id, "test-req")
            assert result.decision == SecurityState.ALLOW, (
                f"{c.chunk_id}: expected ALLOW, got {result.decision} "
                f"reason={result.reason_code}"
            )

    def test_empty_provenance_blocks(self):
        """Empty provenance dict → BLOCK (policy preserved)."""
        result = self.detector.inspect_provenance({}, "test-chunk", "test-req")
        assert result.decision == SecurityState.BLOCK
        assert result.reason_code == "MISSING_PROVENANCE"

    def test_none_provenance_blocks(self):
        """None provenance → BLOCK (policy preserved)."""
        result = self.detector.inspect_provenance(None, "test-chunk", "test-req")
        assert result.decision == SecurityState.BLOCK
        assert result.reason_code == "MISSING_PROVENANCE"

    def test_suspicious_source_blocks(self):
        """Blacklisted source in provenance → BLOCK."""
        result = self.detector.inspect_provenance(
            {"source": "hacked_db"}, "test-chunk", "test-req"
        )
        assert result.decision == SecurityState.BLOCK
        assert result.reason_code == "SUSPICIOUS_SOURCE"

    def test_pubmed_without_docid_blocks(self):
        """PubMed source without document_id → BLOCK."""
        result = self.detector.inspect_provenance(
            {"source": "pubmed"}, "test-chunk", "test-req"
        )
        assert result.decision == SecurityState.BLOCK
        assert result.reason_code == "MISSING_ID"

    def test_fda_source_allows(self):
        """FDA source with document_id → ALLOW."""
        result = self.detector.inspect_provenance(
            {"source": "fda label", "document_id": "doc-1"},
            "test-chunk", "test-req"
        )
        assert result.decision == SecurityState.ALLOW
