"""
Tests for Phase 11 — Claim Verification & Answer Safety Gate.

All pure-Python — no LLM or database required.
Covers: decomposition, alignment, citation check, contradiction detection,
        confidence formula, and full gate decisions (release/qualify/abstain).
"""

from __future__ import annotations

from adaptive_trust_medical_rag.verification.claim_verifier import (
    ALIGNMENT_THRESHOLD,
    ALPHA,
    BETA,
    GAMMA,
    AnswerSafetyGate,
    AtomicClaim,
    EvidenceChunk,
    GateDecision,
    align_claims_to_evidence,
    decompose_into_claims,
    detect_contradictions,
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

WARFARIN_EVIDENCE = EvidenceChunk(
    chunk_id="ev-001",
    text=(
        "Warfarin is an anticoagulant with a narrow therapeutic index. "
        "Concurrent use with aspirin substantially increases the risk of bleeding. "
        "Contraindicated in patients with active bleeding disorders."
    ),
    source_authority=0.95,
    citation_index=1,
)

METFORMIN_EVIDENCE = EvidenceChunk(
    chunk_id="ev-002",
    text=(
        "Metformin hydrochloride is contraindicated in patients with renal impairment "
        "due to the risk of lactic acidosis. "
        "Dosage adjustment is required for hepatic dysfunction."
    ),
    source_authority=0.92,
    citation_index=2,
)

ASPIRIN_EVIDENCE = EvidenceChunk(
    chunk_id="ev-003",
    text=(
        "Aspirin inhibits platelet aggregation. "
        "Concurrent use with anticoagulants such as warfarin increases bleeding risk. "
        "Low-dose aspirin is used for cardiovascular prevention."
    ),
    source_authority=0.90,
    citation_index=3,
)

ALL_EVIDENCE = [WARFARIN_EVIDENCE, METFORMIN_EVIDENCE, ASPIRIN_EVIDENCE]

# A well-grounded answer about warfarin
GROUNDED_ANSWER = (
    "Warfarin is an anticoagulant used for prevention of thromboembolic events [Source 1]. "
    "Concurrent use with aspirin substantially increases the risk of bleeding [Source 1]. "
    "Patients with active bleeding disorders should not receive warfarin "
    "due to contraindication [Source 1]."
)

# An answer with absolute/unsafe language (ungrounded critical claim)
UNSAFE_ANSWER = (
    "Warfarin is completely safe for all patients without any risk of bleeding. "
    "It can be used with aspirin and never causes adverse interactions. "
    "Contraindications do not apply in standard clinical settings."
)

# An answer with one ungrounded non-critical claim
PARTIALLY_GROUNDED_ANSWER = (
    "Warfarin is an anticoagulant with a narrow therapeutic index [Source 1]. "
    "Aspirin inhibits platelet aggregation [Source 3]. "
    "Some patients prefer vegetable-based diets which may affect drug absorption."
)


# ---------------------------------------------------------------------------
# Stage 1: Claim Decomposition
# ---------------------------------------------------------------------------


class TestDecomposeIntoClaims:
    def test_multi_sentence_answer_produces_multiple_claims(self) -> None:
        claims = decompose_into_claims(GROUNDED_ANSWER)
        assert len(claims) >= 2

    def test_claims_have_correct_text(self) -> None:
        claims = decompose_into_claims("Warfarin is an anticoagulant. Aspirin inhibits platelets.")
        texts = [c.text for c in claims]
        assert any("warfarin" in t.lower() for t in texts)
        assert any("aspirin" in t.lower() for t in texts)

    def test_citation_ids_extracted(self) -> None:
        claims = decompose_into_claims(GROUNDED_ANSWER)
        cited = [c for c in claims if c.citation_ids]
        assert len(cited) >= 1
        assert 1 in cited[0].citation_ids

    def test_critical_flag_set_for_absolute_language(self) -> None:
        claims = decompose_into_claims(UNSAFE_ANSWER)
        assert any(c.is_critical for c in claims)

    def test_critical_flag_not_set_for_grounded_answer(self) -> None:
        claims = decompose_into_claims(GROUNDED_ANSWER)
        assert not any(c.is_critical for c in claims)

    def test_drug_entities_extracted(self) -> None:
        claims = decompose_into_claims("Warfarin 5mg is contraindicated with aspirin.")
        drug_ents = [e for c in claims for e in c.drug_entities]
        assert any("warfarin" in e for e in drug_ents)

    def test_empty_answer_returns_empty(self) -> None:
        assert decompose_into_claims("") == []

    def test_very_short_sentence_filtered(self) -> None:
        claims = decompose_into_claims("Yes. Warfarin is an anticoagulant with narrow index.")
        # "Yes." is < 10 chars — filtered
        assert all(len(c.text) >= 10 for c in claims)

    def test_claim_indices_assigned(self) -> None:
        claims = decompose_into_claims(GROUNDED_ANSWER)
        assert all(isinstance(c.claim_index, int) for c in claims)


# ---------------------------------------------------------------------------
# Stage 2 & 3: Alignment & Citation Integrity
# ---------------------------------------------------------------------------


class TestAlignClaimsToEvidence:
    def _make_claim(self, text: str, citation_ids: list[int] | None = None) -> AtomicClaim:
        return AtomicClaim(
            text=text,
            claim_index=0,
            citation_ids=citation_ids or [],
        )

    def test_grounded_claim_scores_above_threshold(self) -> None:
        claim = self._make_claim(
            "Warfarin is contraindicated in patients with active bleeding."
        )
        results = align_claims_to_evidence([claim], ALL_EVIDENCE)
        assert results[0].alignment_score >= ALIGNMENT_THRESHOLD

    def test_unrelated_claim_scores_below_threshold(self) -> None:
        claim = self._make_claim(
            "Quantum computing will revolutionise portfolio management strategies."
        )
        results = align_claims_to_evidence([claim], ALL_EVIDENCE)
        assert results[0].alignment_score < ALIGNMENT_THRESHOLD

    def test_is_grounded_flag_set_correctly(self) -> None:
        grounded = self._make_claim("Warfarin increases bleeding risk with aspirin.")
        ungrounded = self._make_claim("Bananas reduce cholesterol through flavonoid pathways.")
        results = align_claims_to_evidence([grounded, ungrounded], ALL_EVIDENCE)
        assert results[0].is_grounded
        assert not results[1].is_grounded

    def test_valid_citation_passes(self) -> None:
        claim = self._make_claim(
            "Warfarin is an anticoagulant contraindicated in bleeding disorders [Source 1].",
            citation_ids=[1],
        )
        results = align_claims_to_evidence([claim], ALL_EVIDENCE)
        assert results[0].citation_valid

    def test_invalid_citation_id_fails(self) -> None:
        claim = self._make_claim(
            "Warfarin is an anticoagulant [Source 99].",
            citation_ids=[99],
        )
        results = align_claims_to_evidence([claim], ALL_EVIDENCE)
        assert not results[0].citation_valid

    def test_no_citation_does_not_fail_validation(self) -> None:
        claim = self._make_claim("Warfarin is an anticoagulant.")
        results = align_claims_to_evidence([claim], ALL_EVIDENCE)
        assert results[0].citation_valid  # no citation = no violation

    def test_best_chunk_id_set(self) -> None:
        claim = self._make_claim("Warfarin bleeding risk anticoagulant contraindicated.")
        results = align_claims_to_evidence([claim], ALL_EVIDENCE)
        assert results[0].best_chunk_id is not None

    def test_empty_evidence_all_ungrounded(self) -> None:
        claim = self._make_claim("Warfarin is an anticoagulant.")
        results = align_claims_to_evidence([claim], [])
        assert not results[0].is_grounded
        assert results[0].alignment_score == 0.0

    def test_alignment_score_bounded_0_to_1(self) -> None:
        claims = decompose_into_claims(GROUNDED_ANSWER)
        results = align_claims_to_evidence(claims, ALL_EVIDENCE)
        for r in results:
            assert 0.0 <= r.alignment_score <= 1.0


# ---------------------------------------------------------------------------
# Stage 4: Contradiction Detection
# ---------------------------------------------------------------------------


class TestDetectContradictions:
    def test_absolute_language_flagged_as_critical(self) -> None:
        claims = decompose_into_claims(
            "Warfarin is completely safe and never causes bleeding complications."
        )
        flags = detect_contradictions(claims, ALL_EVIDENCE)
        critical = [f for f in flags if f.severity == "critical"]
        assert len(critical) >= 1

    def test_clean_answer_no_contradictions(self) -> None:
        claims = decompose_into_claims(GROUNDED_ANSWER)
        flags = detect_contradictions(claims, ALL_EVIDENCE)
        critical = [f for f in flags if f.severity == "critical"]
        assert len(critical) == 0

    def test_contradiction_flag_has_description(self) -> None:
        claims = decompose_into_claims(UNSAFE_ANSWER)
        flags = detect_contradictions(claims, ALL_EVIDENCE)
        assert all(isinstance(f.description, str) and len(f.description) > 0 for f in flags)

    def test_no_claims_no_contradictions(self) -> None:
        flags = detect_contradictions([], ALL_EVIDENCE)
        assert flags == []

    def test_contradiction_score_bounded(self) -> None:
        claims = decompose_into_claims(UNSAFE_ANSWER)
        flags = detect_contradictions(claims, ALL_EVIDENCE)
        score = len([f for f in flags if f.severity == "critical"]) / max(len(claims), 1)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Confidence Formula
# ---------------------------------------------------------------------------


class TestConfidenceFormula:
    def test_perfect_confidence(self) -> None:
        # grounding=1.0, citation_trust=1.0, contradiction=0.0
        # confidence = 0.4*1 + 0.4*1 + 0.2*(1-0) = 1.0
        c = ALPHA * 1.0 + BETA * 1.0 + GAMMA * (1.0 - 0.0)
        assert abs(c - 1.0) < 1e-9

    def test_zero_confidence(self) -> None:
        # grounding=0, citation_trust=0, contradiction=1
        # confidence = 0.4*0 + 0.4*0 + 0.2*(1-1) = 0.0
        c = ALPHA * 0.0 + BETA * 0.0 + GAMMA * (1.0 - 1.0)
        assert abs(c - 0.0) < 1e-9

    def test_weights_sum_to_one(self) -> None:
        assert abs(ALPHA + BETA + GAMMA - 1.0) < 1e-9

    def test_confidence_bounded_0_to_1(self) -> None:
        gate = AnswerSafetyGate(risk_tier="R1")
        report = gate.verify(GROUNDED_ANSWER, ALL_EVIDENCE)
        assert 0.0 <= report.confidence <= 1.0


# ---------------------------------------------------------------------------
# Stage 5: Answer Safety Gate — full integration
# ---------------------------------------------------------------------------


class TestAnswerSafetyGate:
    def test_grounded_answer_releases(self) -> None:
        gate = AnswerSafetyGate(risk_tier="R0")
        report = gate.verify(GROUNDED_ANSWER, ALL_EVIDENCE)
        assert report.decision == GateDecision.release

    def test_unsafe_answer_abstains(self) -> None:
        gate = AnswerSafetyGate(risk_tier="R2")
        report = gate.verify(UNSAFE_ANSWER, ALL_EVIDENCE)
        assert report.decision == GateDecision.abstain

    def test_partially_grounded_qualifies_or_releases(self) -> None:
        gate = AnswerSafetyGate(risk_tier="R0", confidence_threshold=0.30)
        report = gate.verify(PARTIALLY_GROUNDED_ANSWER, ALL_EVIDENCE)
        assert report.decision in (GateDecision.release, GateDecision.qualify)

    def test_qualify_sets_qualified_answer(self) -> None:
        gate = AnswerSafetyGate(risk_tier="R2", confidence_threshold=0.95)
        report = gate.verify(PARTIALLY_GROUNDED_ANSWER, ALL_EVIDENCE)
        if report.decision == GateDecision.qualify:
            assert report.qualified_answer is not None
            assert "Note: insufficient evidence" in report.qualified_answer

    def test_empty_answer_abstains(self) -> None:
        gate = AnswerSafetyGate()
        report = gate.verify("", ALL_EVIDENCE)
        assert report.decision == GateDecision.abstain

    def test_no_evidence_abstains(self) -> None:
        gate = AnswerSafetyGate(risk_tier="R2")
        report = gate.verify(GROUNDED_ANSWER, [])
        assert report.decision == GateDecision.abstain

    def test_report_contains_all_fields(self) -> None:
        gate = AnswerSafetyGate()
        report = gate.verify(GROUNDED_ANSWER, ALL_EVIDENCE)
        assert isinstance(report.claims, list)
        assert isinstance(report.alignments, list)
        assert isinstance(report.contradictions, list)
        assert isinstance(report.grounding_ratio, float)
        assert isinstance(report.mean_citation_trust, float)
        assert isinstance(report.contradiction_score, float)
        assert isinstance(report.confidence, float)
        assert isinstance(report.explanation, str)

    def test_grounding_ratio_between_0_and_1(self) -> None:
        gate = AnswerSafetyGate()
        report = gate.verify(GROUNDED_ANSWER, ALL_EVIDENCE)
        assert 0.0 <= report.grounding_ratio <= 1.0

    def test_explanation_non_empty(self) -> None:
        gate = AnswerSafetyGate()
        report = gate.verify(GROUNDED_ANSWER, ALL_EVIDENCE)
        assert len(report.explanation) > 0

    def test_r3_threshold_is_075(self) -> None:
        gate = AnswerSafetyGate(risk_tier="R3")
        assert gate.confidence_threshold == 0.75

    def test_r0_threshold_is_030(self) -> None:
        gate = AnswerSafetyGate(risk_tier="R0")
        assert gate.confidence_threshold == 0.30

    def test_ungrounded_claims_property(self) -> None:
        gate = AnswerSafetyGate(risk_tier="R0")
        report = gate.verify(PARTIALLY_GROUNDED_ANSWER, ALL_EVIDENCE)
        for ar in report.ungrounded_claims:
            assert not ar.is_grounded

    def test_critical_ungrounded_property(self) -> None:
        gate = AnswerSafetyGate(risk_tier="R2")
        report = gate.verify(UNSAFE_ANSWER, ALL_EVIDENCE)
        for ar in report.critical_ungrounded:
            assert ar.claim.is_critical
            assert not ar.is_grounded
