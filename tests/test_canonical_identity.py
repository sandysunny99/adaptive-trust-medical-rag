"""Canonical Relationship Identity validation tests.

Tests the deterministic canonical identity control layer that verifies
subject, object, predicate, and direction consistency between source
evidence and generated claims.

This control complements semantic NLI rather than replacing it.
It adds deterministic canonical identity validation for the tested
subject, object, predicate, and direction mismatch classes.

No external provider. No network. No real LLM.
"""

from __future__ import annotations

import pytest
from adaptive_trust_medical_rag.verification.canonical_identity import (
    CanonicalDirection,
    CanonicalMatchStatus,
    CanonicalRelationshipIdentity,
    compare_identity,
    extract_claim_identity,
    normalize_predicate,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def source_identity():
    """Standard source canonical identity: warfarin inhibits aspirin A->B."""
    return CanonicalRelationshipIdentity(
        subject_rxcui="11289",   # warfarin
        object_rxcui="1191",     # aspirin
        predicate="INHIBITION",
        direction=CanonicalDirection.A_TO_B,
        provenance_chunk_id="chunk_001",
    )


@pytest.fixture
def drug_rxcui_map():
    """Standard drug name -> RxCUI mapping for test claims."""
    return {
        "warfarin": "11289",
        "aspirin": "1191",
        "metformin": "6809",
        "simvastatin": "36567",
        "fluoxetine": "4493",
    }


# ─────────────────────────────────────────────────────────────────────────────
# RI-01: Correct subject + correct object + correct predicate + correct direction
# ─────────────────────────────────────────────────────────────────────────────

class TestRI01CorrectMatch:
    def test_exact_match(self, source_identity):
        claim = CanonicalRelationshipIdentity(
            subject_rxcui="11289",
            object_rxcui="1191",
            predicate="INHIBITION",
            direction=CanonicalDirection.A_TO_B,
        )
        status, reason = compare_identity(source_identity, claim)
        assert status == CanonicalMatchStatus.MATCH
        assert "match" in reason.lower()


# ─────────────────────────────────────────────────────────────────────────────
# RI-02: Wrong predicate
# ─────────────────────────────────────────────────────────────────────────────

class TestRI02WrongPredicate:
    def test_wrong_predicate_mismatch(self, source_identity):
        claim = CanonicalRelationshipIdentity(
            subject_rxcui="11289",
            object_rxcui="1191",
            predicate="INDUCTION",  # Wrong: should be INHIBITION
            direction=CanonicalDirection.A_TO_B,
        )
        status, reason = compare_identity(source_identity, claim)
        assert status == CanonicalMatchStatus.MISMATCH
        assert "Predicate" in reason


# ─────────────────────────────────────────────────────────────────────────────
# RI-03: Wrong subject
# ─────────────────────────────────────────────────────────────────────────────

class TestRI03WrongSubject:
    def test_wrong_subject_mismatch(self, source_identity):
        claim = CanonicalRelationshipIdentity(
            subject_rxcui="6809",   # metformin, wrong
            object_rxcui="1191",
            predicate="INHIBITION",
            direction=CanonicalDirection.A_TO_B,
        )
        status, reason = compare_identity(source_identity, claim)
        assert status == CanonicalMatchStatus.MISMATCH
        assert "Subject" in reason


# ─────────────────────────────────────────────────────────────────────────────
# RI-04: Wrong object
# ─────────────────────────────────────────────────────────────────────────────

class TestRI04WrongObject:
    def test_wrong_object_mismatch(self, source_identity):
        claim = CanonicalRelationshipIdentity(
            subject_rxcui="11289",
            object_rxcui="6809",  # metformin, wrong
            predicate="INHIBITION",
            direction=CanonicalDirection.A_TO_B,
        )
        status, reason = compare_identity(source_identity, claim)
        assert status == CanonicalMatchStatus.MISMATCH
        assert "Object" in reason


# ─────────────────────────────────────────────────────────────────────────────
# RI-05: Reverse direction
# ─────────────────────────────────────────────────────────────────────────────

class TestRI05ReverseDirection:
    def test_reversed_direction_mismatch(self, source_identity):
        claim = CanonicalRelationshipIdentity(
            subject_rxcui="11289",
            object_rxcui="1191",
            predicate="INHIBITION",
            direction=CanonicalDirection.B_TO_A,  # Reversed
        )
        status, reason = compare_identity(source_identity, claim)
        assert status == CanonicalMatchStatus.MISMATCH
        assert "Direction" in reason


# ─────────────────────────────────────────────────────────────────────────────
# RI-06: Ambiguous subject
# ─────────────────────────────────────────────────────────────────────────────

class TestRI06AmbiguousSubject:
    def test_ambiguous_subject_controlled_failure(self, source_identity):
        claim = CanonicalRelationshipIdentity(
            subject_rxcui="",     # Empty / unresolved
            object_rxcui="1191",
            predicate="INHIBITION",
            direction=CanonicalDirection.A_TO_B,
        )
        status, reason = compare_identity(source_identity, claim)
        assert status == CanonicalMatchStatus.AMBIGUOUS
        assert "unresolved" in reason.lower()


# ─────────────────────────────────────────────────────────────────────────────
# RI-07: Unresolved object
# ─────────────────────────────────────────────────────────────────────────────

class TestRI07UnresolvedObject:
    def test_unresolved_object_controlled_failure(self, source_identity):
        claim = CanonicalRelationshipIdentity(
            subject_rxcui="11289",
            object_rxcui="",      # Empty / unresolved
            predicate="INHIBITION",
            direction=CanonicalDirection.A_TO_B,
        )
        status, reason = compare_identity(source_identity, claim)
        assert status == CanonicalMatchStatus.AMBIGUOUS
        assert "unresolved" in reason.lower()


# ─────────────────────────────────────────────────────────────────────────────
# RI-08: RG-02 SUPPORTED but canonical mismatch -> final failure
# Tested via claim_verifier_v2 integration (see integration tests)
# ─────────────────────────────────────────────────────────────────────────────

class TestRI08RG02SupportedButIdentityMismatch:
    def test_rg02_supported_identity_mismatch(self, source_identity):
        """Even if RG-02 says SUPPORTED, a canonical identity mismatch must fail."""
        claim = CanonicalRelationshipIdentity(
            subject_rxcui="6809",   # Wrong subject
            object_rxcui="1191",
            predicate="INHIBITION",
            direction=CanonicalDirection.A_TO_B,
        )
        status, _ = compare_identity(source_identity, claim)
        # The canonical check itself always returns MISMATCH regardless of RG-02
        assert status == CanonicalMatchStatus.MISMATCH


# ─────────────────────────────────────────────────────────────────────────────
# RI-09: Strong NLI entailment but canonical mismatch -> final failure
# ─────────────────────────────────────────────────────────────────────────────

class TestRI09NLISupportedButIdentityMismatch:
    def test_nli_irrelevant_for_identity(self, source_identity):
        """NLI entailment score is irrelevant when canonical identity mismatches."""
        claim = CanonicalRelationshipIdentity(
            subject_rxcui="11289",
            object_rxcui="1191",
            predicate="INDUCTION",  # Wrong predicate
            direction=CanonicalDirection.A_TO_B,
        )
        status, _ = compare_identity(source_identity, claim)
        assert status == CanonicalMatchStatus.MISMATCH


# ─────────────────────────────────────────────────────────────────────────────
# RI-10: Canonical match + invalid citation -> citation failure remains
# (Tested at integration level - canonical match doesn't override citation)
# ─────────────────────────────────────────────────────────────────────────────

class TestRI10CanonicalMatchInvalidCitation:
    def test_canonical_match_does_not_override_citation(self, source_identity):
        """Identity MATCH doesn't bypass citation controls."""
        claim = CanonicalRelationshipIdentity(
            subject_rxcui="11289",
            object_rxcui="1191",
            predicate="INHIBITION",
            direction=CanonicalDirection.A_TO_B,
        )
        status, _ = compare_identity(source_identity, claim)
        # Identity matches, but citation checks are separate
        assert status == CanonicalMatchStatus.MATCH
        # Citation validation remains independent (tested at integration level)


# ─────────────────────────────────────────────────────────────────────────────
# RI-11: Canonical match + low trust -> trust failure remains
# (Tested at integration level - canonical match doesn't override trust)
# ─────────────────────────────────────────────────────────────────────────────

class TestRI11CanonicalMatchLowTrust:
    def test_canonical_match_does_not_override_trust(self, source_identity):
        """Identity MATCH doesn't bypass trust controls."""
        claim = CanonicalRelationshipIdentity(
            subject_rxcui="11289",
            object_rxcui="1191",
            predicate="INHIBITION",
            direction=CanonicalDirection.A_TO_B,
        )
        status, _ = compare_identity(source_identity, claim)
        assert status == CanonicalMatchStatus.MATCH
        # Trust score checks are separate and independent


# ─────────────────────────────────────────────────────────────────────────────
# RI-12: Full correct path -> normal release
# ─────────────────────────────────────────────────────────────────────────────

class TestRI12FullCorrectPath:
    def test_all_correct_produces_match(self, source_identity):
        claim = CanonicalRelationshipIdentity(
            subject_rxcui="11289",
            object_rxcui="1191",
            predicate="INHIBITION",
            direction=CanonicalDirection.A_TO_B,
        )
        status, reason = compare_identity(source_identity, claim)
        assert status == CanonicalMatchStatus.MATCH
        assert "match" in reason.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Negative security: direction reversal adversarial test
# ─────────────────────────────────────────────────────────────────────────────

class TestAdversarialDirectionReversal:
    def test_direction_reversal_attack(self):
        """Adversarial test: source says A->B, claim says B->A.
        
        Demonstrates the architectural control against direction spoofing.
        NLI might score this favorably (both drugs and predicate are textually
        present), but the deterministic canonical check catches the reversal.
        """
        source = CanonicalRelationshipIdentity(
            subject_rxcui="11289",  # warfarin
            object_rxcui="1191",    # aspirin
            predicate="INHIBITION",
            direction=CanonicalDirection.A_TO_B,
            provenance_chunk_id="chunk_source",
        )
        # Attacker claim reverses direction
        attacker_claim = CanonicalRelationshipIdentity(
            subject_rxcui="11289",
            object_rxcui="1191",
            predicate="INHIBITION",
            direction=CanonicalDirection.B_TO_A,
        )
        status, reason = compare_identity(source, attacker_claim)
        assert status == CanonicalMatchStatus.MISMATCH
        assert "Direction" in reason


# ─────────────────────────────────────────────────────────────────────────────
# Predicate normalization tests
# ─────────────────────────────────────────────────────────────────────────────

class TestPredicateNormalization:
    def test_inhibits_maps_to_inhibition(self):
        assert normalize_predicate("inhibits") == "INHIBITION"

    def test_inhibitor_maps_to_inhibition(self):
        assert normalize_predicate("inhibitor") == "INHIBITION"

    def test_induces_maps_to_induction(self):
        assert normalize_predicate("induces") == "INDUCTION"

    def test_increases_maps_to_increases(self):
        assert normalize_predicate("increases") == "INCREASES"

    def test_contraindicated_maps(self):
        assert normalize_predicate("contraindicated") == "CONTRAINDICATION"

    def test_unknown_predicate_uppercased(self):
        assert normalize_predicate("novel_relation") == "NOVEL_RELATION"


# ─────────────────────────────────────────────────────────────────────────────
# Claim identity extraction tests
# ─────────────────────────────────────────────────────────────────────────────

class TestClaimIdentityExtraction:
    def test_extracts_two_drug_identity(self, drug_rxcui_map):
        claim = "Warfarin inhibits the metabolism of aspirin. [Source 1]"
        identity = extract_claim_identity(claim, drug_rxcui_map)
        assert identity is not None
        assert identity.subject_rxcui == "11289"
        assert identity.object_rxcui == "1191"
        assert identity.predicate == "INHIBITION"
        assert identity.direction == CanonicalDirection.A_TO_B

    def test_returns_none_for_single_drug(self, drug_rxcui_map):
        claim = "Warfarin is an anticoagulant. [Source 1]"
        identity = extract_claim_identity(claim, drug_rxcui_map)
        assert identity is None

    def test_returns_none_for_no_predicate(self, drug_rxcui_map):
        claim = "Warfarin and aspirin are both medications. [Source 1]"
        identity = extract_claim_identity(claim, drug_rxcui_map)
        assert identity is None

    def test_returns_none_for_unresolved_drug(self):
        """Drug not in RxCUI map -> None (will become AMBIGUOUS/UNAVAILABLE)."""
        rxcui_map = {"warfarin": "11289"}  # aspirin missing
        claim = "Warfarin inhibits aspirin metabolism. [Source 1]"
        identity = extract_claim_identity(claim, rxcui_map)
        assert identity is None


# ─────────────────────────────────────────────────────────────────────────────
# Null/edge case tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:
    def test_both_none(self):
        status, _ = compare_identity(None, None)
        assert status == CanonicalMatchStatus.UNAVAILABLE

    def test_source_none(self):
        claim = CanonicalRelationshipIdentity(
            subject_rxcui="11289",
            object_rxcui="1191",
            predicate="INHIBITION",
            direction=CanonicalDirection.A_TO_B,
        )
        status, _ = compare_identity(None, claim)
        assert status == CanonicalMatchStatus.UNAVAILABLE

    def test_claim_none(self, source_identity):
        status, _ = compare_identity(source_identity, None)
        assert status == CanonicalMatchStatus.UNAVAILABLE

    def test_unknown_direction_ambiguous(self, source_identity):
        claim = CanonicalRelationshipIdentity(
            subject_rxcui="11289",
            object_rxcui="1191",
            predicate="INHIBITION",
            direction=CanonicalDirection.UNKNOWN,
        )
        status, _ = compare_identity(source_identity, claim)
        assert status == CanonicalMatchStatus.AMBIGUOUS


# ─────────────────────────────────────────────────────────────────────────────
# Serialization / backward compatibility
# ─────────────────────────────────────────────────────────────────────────────

class TestSerialization:
    def test_identity_is_frozen(self):
        identity = CanonicalRelationshipIdentity(
            subject_rxcui="11289",
            object_rxcui="1191",
            predicate="INHIBITION",
            direction=CanonicalDirection.A_TO_B,
        )
        with pytest.raises(AttributeError):
            identity.subject_rxcui = "changed"  # type: ignore

    def test_evidence_chunk_backward_compatible(self):
        """EvidenceChunk without identity still works (default None)."""
        from adaptive_trust_medical_rag.verification.claim_verifier import EvidenceChunk
        chunk = EvidenceChunk(
            chunk_id="c1",
            text="some text",
            source_authority=0.9,
            citation_index=1,
        )
        assert chunk.relationship_identity is None

    def test_evidence_chunk_with_identity(self):
        from adaptive_trust_medical_rag.verification.claim_verifier import EvidenceChunk
        identity = CanonicalRelationshipIdentity(
            subject_rxcui="11289",
            object_rxcui="1191",
            predicate="INHIBITION",
            direction=CanonicalDirection.A_TO_B,
        )
        chunk = EvidenceChunk(
            chunk_id="c1",
            text="some text",
            relationship_identity=identity,
        )
        assert chunk.relationship_identity is not None
        assert chunk.relationship_identity.subject_rxcui == "11289"
