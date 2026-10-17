"""Unit tests for AI-assisted annotation schemas, loaders, reviewers, engine, and commit modules.

Verifies strict provenance, non-destructive behavior, and label-grade consistency.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from adaptive_trust_medical_rag.annotation.commit import (
    commit_researcher_decisions,
)
from adaptive_trust_medical_rag.annotation.engine import (
    AIAnnotationEngine,
    PromptHashMismatchError,
)
from adaptive_trust_medical_rag.annotation.loader import (
    load_annotator_file,
    load_unannotated,
    save_ai_recommendations,
    save_researcher_decisions,
)
from adaptive_trust_medical_rag.annotation.reviewer import (
    format_position_for_review,
    generate_batch_review_report,
    generate_summary_statistics,
)
from adaptive_trust_medical_rag.annotation.schemas import (
    LABEL_TO_GRADE_MAP,
    AIRecommendation,
    AlignmentType,
    AnnotationBatch,
    AnnotationPosition,
    AnnotationSessionConfig,
    ClaimPolarity,
    ClaimType,
    ConfidenceLevel,
    EvidenceClaim,
    PolarityType,
    RelevanceLabel,
    ResearcherAction,
    ResearcherDecision,
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
ANNOTATOR_A_PATH = WORKSPACE_ROOT / "track_a_annotation" / "annotator_a" / "TRACK_A_ANNOTATOR_A.jsonl"


# ==============================================================================
# 1. Tests for Pydantic Schemas
# ==============================================================================


class TestAnnotationPositionSchema:
    def test_minimal_valid_position(self):
        pos = AnnotationPosition(
            position_id="pos-001",
            query_id="q-001",
            query_text="Clearance pathway for lisinopril",
            chunk_id="chunk-001",
            document_id="doc-001",
            retrieved_evidence="Lisinopril is primarily excreted unchanged by the kidneys.",
        )
        assert pos.position_id == "pos-001"
        assert pos.annotation_status == "UNANNOTATED"
        assert pos.schema_version == "2.0.0"
        assert pos.abstract_available is True

    def test_position_with_extra_fields(self):
        pos = AnnotationPosition(
            position_id="pos-002",
            query_id="q-002",
            query_text="Warfarin and aspirin interaction",
            chunk_id="chunk-002",
            document_id="doc-002",
            retrieved_evidence="Some text",
            human_confirmation=True,
            llm_assistance="RESEARCH_CONTROL_LLM_ASSISTED",
            grade=1,
            relevance_grade=1,
            extra_field="custom_value",
        )
        assert pos.human_confirmation is True
        assert pos.grade == 1
        assert getattr(pos, "extra_field", None) == "custom_value"


class TestAIRecommendationSchema:
    @pytest.fixture
    def valid_recommendation_data(self) -> dict[str, Any]:
        return {
            "query_entities": ["lisinopril"],
            "requested_property": "clearance pathway",
            "requested_relation": None,
            "requested_outcome": None,
            "entity_alignment": AlignmentType.EXACT,
            "relationship_alignment": AlignmentType.EXACT,
            "relationship_polarity": PolarityType.POSITIVE,
            "outcome_alignment": AlignmentType.NOT_APPLICABLE,
            "outcome_polarity": PolarityType.NOT_APPLICABLE,
            "evidence_claims": [
                {
                    "claim_text": "Lisinopril is excreted unchanged in urine.",
                    "evidence_span": "excreted unchanged in urine",
                    "claim_type": ClaimType.PHARMACOKINETIC,
                    "polarity": ClaimPolarity.POSITIVE,
                }
            ],
            "supported_claims": ["Lisinopril undergoes renal elimination."],
            "unsupported_claims": [],
            "missing_information": [],
            "counterevidence": [],
            "uncertainties": [],
            "best_supporting_span": "excreted unchanged in urine",
            "proposed_label": RelevanceLabel.RELEVANT,
            "proposed_grade": 2,
            "proposed_rationale": "Evidence directly identifies renal clearance pathway.",
            "confidence": ConfidenceLevel.HIGH,
            "alternative_label_considered": None,
        }

    def test_valid_21_fields_recommendation(self, valid_recommendation_data):
        rec = AIRecommendation.model_validate(valid_recommendation_data)
        assert rec.proposed_label == RelevanceLabel.RELEVANT
        assert rec.proposed_grade == 2
        assert len(rec.evidence_claims) == 1
        assert rec.confidence == ConfidenceLevel.HIGH

    @pytest.mark.parametrize(
        "label,grade,should_succeed",
        [
            (RelevanceLabel.RELEVANT, 2, True),
            (RelevanceLabel.RELEVANT, 1, False),
            (RelevanceLabel.RELEVANT, 0, False),
            (RelevanceLabel.PARTIALLY_RELEVANT, 1, True),
            (RelevanceLabel.PARTIALLY_RELEVANT, 2, False),
            (RelevanceLabel.IRRELEVANT, 0, True),
            (RelevanceLabel.IRRELEVANT, 1, False),
            (RelevanceLabel.INSUFFICIENT_INFORMATION, 0, True),
            (RelevanceLabel.INSUFFICIENT_INFORMATION, 1, False),
            (RelevanceLabel.AMBIGUOUS, None, True),
            (RelevanceLabel.AMBIGUOUS, 0, False),
        ],
    )
    def test_label_grade_consistency(self, valid_recommendation_data, label, grade, should_succeed):
        valid_recommendation_data["proposed_label"] = label
        valid_recommendation_data["proposed_grade"] = grade
        if label == RelevanceLabel.IRRELEVANT:
            valid_recommendation_data["best_supporting_span"] = ""

        if should_succeed:
            rec = AIRecommendation.model_validate(valid_recommendation_data)
            assert rec.proposed_grade == grade
        else:
            with pytest.raises(ValueError, match="Proposed grade"):
                AIRecommendation.model_validate(valid_recommendation_data)

    def test_span_validation(self, valid_recommendation_data):
        rec = AIRecommendation.model_validate(valid_recommendation_data)
        evidence = "Pharmacokinetics: Lisinopril is excreted unchanged in urine without metabolism."
        errors = rec.validate_spans(evidence)
        assert len(errors) == 0

        # Tampered evidence missing span
        tampered_evidence = "Pharmacokinetics: The drug is removed by dialysis."
        errors = rec.validate_spans(tampered_evidence)
        assert len(errors) > 0
        assert any("best_supporting_span" in err for err in errors)

    def test_empty_span_handling(self, valid_recommendation_data):
        # Empty span should fail for RELEVANT
        valid_recommendation_data["best_supporting_span"] = ""
        rec = AIRecommendation.model_validate(valid_recommendation_data)
        errors = rec.validate_spans("Some evidence text")
        assert any("best_supporting_span is required" in err for err in errors)

        # Empty span should be allowed for IRRELEVANT
        valid_recommendation_data["proposed_label"] = RelevanceLabel.IRRELEVANT
        valid_recommendation_data["proposed_grade"] = 0
        valid_recommendation_data["evidence_claims"] = []
        rec_irrelevant = AIRecommendation.model_validate(valid_recommendation_data)
        errors_irrelevant = rec_irrelevant.validate_spans("Any text")
        assert len(errors_irrelevant) == 0


class TestResearcherDecisionSchema:
    @pytest.fixture
    def sample_recommendation(self) -> AIRecommendation:
        return AIRecommendation(
            query_entities=["warfarin", "aspirin"],
            requested_property=None,
            requested_relation="drug interaction",
            requested_outcome="bleeding risk",
            entity_alignment=AlignmentType.EXACT,
            relationship_alignment=AlignmentType.EXACT,
            relationship_polarity=PolarityType.POSITIVE,
            outcome_alignment=AlignmentType.EXACT,
            outcome_polarity=PolarityType.POSITIVE,
            evidence_claims=[],
            supported_claims=["Coadministration increases major bleeding risk."],
            unsupported_claims=[],
            missing_information=[],
            counterevidence=[],
            uncertainties=[],
            best_supporting_span="increases major bleeding risk",
            proposed_label=RelevanceLabel.RELEVANT,
            proposed_grade=2,
            proposed_rationale="Explicitly states increased bleeding risk.",
            confidence=ConfidenceLevel.HIGH,
            alternative_label_considered=None,
        )

    def test_approve_action_auto_populates(self, sample_recommendation):
        decision = ResearcherDecision(
            position_id="pos-001",
            recommendation=sample_recommendation,
            researcher_action=ResearcherAction.APPROVE,
        )
        assert decision.final_label == RelevanceLabel.RELEVANT
        assert decision.final_grade == 2
        assert decision.final_evidence_span == "increases major bleeding risk"
        assert "Approved AI recommendation" in decision.researcher_rationale

    def test_override_action_requires_rationale(self, sample_recommendation):
        with pytest.raises(ValueError, match="OVERRIDE action requires researcher_rationale"):
            ResearcherDecision(
                position_id="pos-001",
                recommendation=sample_recommendation,
                researcher_action=ResearcherAction.OVERRIDE,
                final_label=RelevanceLabel.PARTIALLY_RELEVANT,
                researcher_rationale="",
            )

    def test_override_action_populates_grade(self, sample_recommendation):
        decision = ResearcherDecision(
            position_id="pos-001",
            recommendation=sample_recommendation,
            researcher_action=ResearcherAction.OVERRIDE,
            final_label=RelevanceLabel.PARTIALLY_RELEVANT,
            researcher_rationale="Evidence only covers mechanistic interaction, not clinical risk outcome.",
            final_evidence_span="mechanistic interaction observed",
        )
        assert decision.final_grade == 1
        assert decision.final_label == RelevanceLabel.PARTIALLY_RELEVANT


class TestAnnotationConfigAndBatch:
    def test_config_hash_deterministic(self):
        cfg1 = AnnotationSessionConfig(provider="groq", model="openai/gpt-oss-120b", seed=42)
        cfg2 = AnnotationSessionConfig(provider="groq", model="openai/gpt-oss-120b", seed=42)
        assert cfg1.compute_config_hash() == cfg2.compute_config_hash()

        cfg3 = AnnotationSessionConfig(provider="groq", model="openai/gpt-oss-120b", seed=99)
        assert cfg1.compute_config_hash() != cfg3.compute_config_hash()

    def test_batch_instantiation(self):
        cfg = AnnotationSessionConfig()
        batch = AnnotationBatch(
            batch_id="BATCH-001",
            config_hash=cfg.compute_config_hash(),
            prompt_hashes={"sys": "hash1", "adj": "hash2"},
        )
        assert batch.batch_id == "BATCH-001"
        assert batch.status == "PENDING"
        assert len(batch.positions) == 0


# ==============================================================================
# 2. Tests for Loader Module
# ==============================================================================


class TestLoaderModule:
    def test_load_real_annotator_file(self):
        assert ANNOTATOR_A_PATH.exists(), f"Missing dataset: {ANNOTATOR_A_PATH}"
        positions = load_annotator_file(ANNOTATOR_A_PATH)
        assert len(positions) == 530

        unannotated = load_unannotated(ANNOTATOR_A_PATH)
        assert len(unannotated) == 429

        annotated = [p for p in positions if p.annotation_status == "ANNOTATED"]
        assert len(annotated) == 101

    def test_save_ai_recommendations_guards_against_human_file(self, tmp_path):
        dummy_pos = AnnotationPosition(
            position_id="pos-test",
            query_id="q-test",
            query_text="query",
            chunk_id="chunk-test",
            document_id="doc-test",
            retrieved_evidence="evidence",
        )
        dummy_rec = AIRecommendation(
            query_entities=["drug"],
            requested_property=None,
            requested_relation=None,
            requested_outcome=None,
            entity_alignment=AlignmentType.EXACT,
            relationship_alignment=AlignmentType.NOT_APPLICABLE,
            relationship_polarity=PolarityType.NOT_APPLICABLE,
            outcome_alignment=AlignmentType.NOT_APPLICABLE,
            outcome_polarity=PolarityType.NOT_APPLICABLE,
            evidence_claims=[],
            supported_claims=[],
            unsupported_claims=[],
            missing_information=[],
            counterevidence=[],
            uncertainties=[],
            best_supporting_span="",
            proposed_label=RelevanceLabel.IRRELEVANT,
            proposed_grade=0,
            proposed_rationale="Irrelevant",
            confidence=ConfidenceLevel.HIGH,
            alternative_label_considered=None,
        )

        # Attempt to save to protected path should raise PermissionError
        forbidden_path = tmp_path / "annotator_a" / "track_a_annotator_a.jsonl"
        with pytest.raises(PermissionError, match="Destructive write rejected"):
            save_ai_recommendations([(dummy_pos, dummy_rec)], forbidden_path)

        # Normal separate path works
        safe_path = tmp_path / "ai_recommendations" / "recommendations.jsonl"
        save_ai_recommendations([(dummy_pos, dummy_rec)], safe_path)
        assert safe_path.exists()

        with open(safe_path, encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["position_id"] == "pos-test"
        assert record["provenance"] == "AI_ASSISTED_V1"
        assert record["recommendation"]["proposed_label"] == "IRRELEVANT"

    def test_save_researcher_decisions(self, tmp_path):
        dummy_rec = AIRecommendation(
            query_entities=["drug"],
            requested_property=None,
            requested_relation=None,
            requested_outcome=None,
            entity_alignment=AlignmentType.EXACT,
            relationship_alignment=AlignmentType.NOT_APPLICABLE,
            relationship_polarity=PolarityType.NOT_APPLICABLE,
            outcome_alignment=AlignmentType.NOT_APPLICABLE,
            outcome_polarity=PolarityType.NOT_APPLICABLE,
            evidence_claims=[],
            supported_claims=[],
            unsupported_claims=[],
            missing_information=[],
            counterevidence=[],
            uncertainties=[],
            best_supporting_span="",
            proposed_label=RelevanceLabel.IRRELEVANT,
            proposed_grade=0,
            proposed_rationale="Irrelevant",
            confidence=ConfidenceLevel.HIGH,
            alternative_label_considered=None,
        )
        decision = ResearcherDecision(
            position_id="pos-001",
            recommendation=dummy_rec,
            researcher_action=ResearcherAction.APPROVE,
        )
        dec_path = tmp_path / "decisions.jsonl"
        save_researcher_decisions([decision], dec_path)
        assert dec_path.exists()

        with open(dec_path, encoding="utf-8") as f:
            data = json.loads(f.readline())
        assert data["position_id"] == "pos-001"
        assert data["final_label"] == "IRRELEVANT"


# ==============================================================================
# 3. Tests for Reviewer Module
# ==============================================================================


class TestReviewerModule:
    @pytest.fixture
    def sample_pair(self) -> tuple[AnnotationPosition, AIRecommendation]:
        pos = AnnotationPosition(
            position_id="pos-test-rev",
            query_id="q-rev",
            query_text="Clearance pathway for lisinopril",
            chunk_id="chunk-rev",
            document_id="doc-rev",
            retrieved_evidence="Lisinopril is removed unchanged by renal clearance.",
        )
        rec = AIRecommendation(
            query_entities=["lisinopril"],
            requested_property="clearance pathway",
            requested_relation=None,
            requested_outcome=None,
            entity_alignment=AlignmentType.EXACT,
            relationship_alignment=AlignmentType.EXACT,
            relationship_polarity=PolarityType.POSITIVE,
            outcome_alignment=AlignmentType.NOT_APPLICABLE,
            outcome_polarity=PolarityType.NOT_APPLICABLE,
            evidence_claims=[
                EvidenceClaim(
                    claim_text="Lisinopril undergoes renal clearance",
                    evidence_span="removed unchanged by renal clearance",
                    claim_type=ClaimType.PHARMACOKINETIC,
                    polarity=ClaimPolarity.POSITIVE,
                )
            ],
            supported_claims=["Renal clearance confirmed."],
            unsupported_claims=[],
            missing_information=[],
            counterevidence=[],
            uncertainties=[],
            best_supporting_span="removed unchanged by renal clearance",
            proposed_label=RelevanceLabel.RELEVANT,
            proposed_grade=2,
            proposed_rationale="Direct renal clearance evidence.",
            confidence=ConfidenceLevel.HIGH,
            alternative_label_considered=None,
        )
        return pos, rec

    def test_format_position_for_review(self, sample_pair):
        pos, rec = sample_pair
        md = format_position_for_review(pos, rec)
        assert "### Position: `pos-test-rev`" in md
        assert "Clearance pathway for lisinopril" in md
        assert "**RELEVANT** (Grade: `2`)" in md
        assert "[ ] **APPROVE**" in md
        assert "[ ] **OVERRIDE**" in md
        assert "[ ] **DEFER**" in md
        assert "removed unchanged by renal clearance" in md

    def test_generate_summary_statistics(self, sample_pair):
        _, rec = sample_pair
        stats = generate_summary_statistics([rec])
        assert stats["total_count"] == 1
        assert stats["label_distribution"]["RELEVANT"]["count"] == 1
        assert stats["confidence_distribution"]["HIGH"]["count"] == 1
        assert stats["spans_present_count"] == 1
        assert stats["claims_total_count"] == 1

    def test_generate_batch_review_report(self, sample_pair, tmp_path):
        out_report = tmp_path / "review_report.md"
        generate_batch_review_report([sample_pair], out_report)
        assert out_report.exists()
        content = out_report.read_text(encoding="utf-8")
        assert "# Track A Medical Evidence Relevance Review Report" in content
        assert "## Batch Summary Statistics" in content
        assert "## Query: Clearance pathway for lisinopril" in content
        assert "pos-test-rev" in content


# ==============================================================================
# 4. Tests for Commit Module
# ==============================================================================


class TestCommitModule:
    @pytest.fixture
    def test_annotator_file(self, tmp_path) -> Path:
        file_path = tmp_path / "annotator_data.jsonl"
        records = [
            {
                "position_id": "pos-already-annotated",
                "query_id": "q1",
                "query_text": "q text",
                "chunk_id": "c1",
                "document_id": "d1",
                "retrieved_evidence": "ev1",
                "annotator_id": "ANNOTATOR_A",
                "relevance_grade": 0,
                "label": "IRRELEVANT",
                "rationale": "Human annotated",
                "evidence_span": None,
                "timestamp": "2026-10-01T00:00:00",
                "schema_version": "2.0.0",
                "annotation_status": "ANNOTATED",
            },
            {
                "position_id": "pos-to-approve",
                "query_id": "q1",
                "query_text": "q text",
                "chunk_id": "c2",
                "document_id": "d2",
                "retrieved_evidence": "ev2 with span",
                "annotator_id": None,
                "relevance_grade": None,
                "label": None,
                "rationale": None,
                "evidence_span": None,
                "timestamp": None,
                "schema_version": "2.0.0",
                "annotation_status": "UNANNOTATED",
            },
            {
                "position_id": "pos-to-override",
                "query_id": "q1",
                "query_text": "q text",
                "chunk_id": "c3",
                "document_id": "d3",
                "retrieved_evidence": "ev3 with span",
                "annotator_id": None,
                "relevance_grade": None,
                "label": None,
                "rationale": None,
                "evidence_span": None,
                "timestamp": None,
                "schema_version": "2.0.0",
                "annotation_status": "UNANNOTATED",
            },
            {
                "position_id": "pos-to-defer",
                "query_id": "q1",
                "query_text": "q text",
                "chunk_id": "c4",
                "document_id": "d4",
                "retrieved_evidence": "ev4",
                "annotator_id": None,
                "relevance_grade": None,
                "label": None,
                "rationale": None,
                "evidence_span": None,
                "timestamp": None,
                "schema_version": "2.0.0",
                "annotation_status": "UNANNOTATED",
            },
        ]
        with open(file_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")
        return file_path

    def test_non_destructive_commit(self, test_annotator_file):
        rec_relevant = AIRecommendation(
            query_entities=["q"],
            requested_property=None,
            requested_relation=None,
            requested_outcome=None,
            entity_alignment=AlignmentType.EXACT,
            relationship_alignment=AlignmentType.EXACT,
            relationship_polarity=PolarityType.POSITIVE,
            outcome_alignment=AlignmentType.NOT_APPLICABLE,
            outcome_polarity=PolarityType.NOT_APPLICABLE,
            evidence_claims=[],
            supported_claims=[],
            unsupported_claims=[],
            missing_information=[],
            counterevidence=[],
            uncertainties=[],
            best_supporting_span="span",
            proposed_label=RelevanceLabel.RELEVANT,
            proposed_grade=2,
            proposed_rationale="Clear evidence.",
            confidence=ConfidenceLevel.HIGH,
            alternative_label_considered=None,
        )

        decisions = [
            # 1. Attempt to overwrite existing ANNOTATED record (must be skipped!)
            ResearcherDecision(
                position_id="pos-already-annotated",
                recommendation=rec_relevant,
                researcher_action=ResearcherAction.APPROVE,
            ),
            # 2. Approve unannotated
            ResearcherDecision(
                position_id="pos-to-approve",
                recommendation=rec_relevant,
                researcher_action=ResearcherAction.APPROVE,
            ),
            # 3. Override unannotated
            ResearcherDecision(
                position_id="pos-to-override",
                recommendation=rec_relevant,
                researcher_action=ResearcherAction.OVERRIDE,
                final_label=RelevanceLabel.PARTIALLY_RELEVANT,
                final_grade=1,
                researcher_rationale="Overriding to partial relevance.",
            ),
            # 4. Defer unannotated (must NOT commit)
            ResearcherDecision(
                position_id="pos-to-defer",
                recommendation=rec_relevant,
                researcher_action=ResearcherAction.DEFER,
            ),
        ]

        summary = commit_researcher_decisions(
            decisions=decisions,
            annotator_file=test_annotator_file,
            provenance_tag="AI_ASSISTED_RESEARCHER_APPROVED",
        )

        assert summary["total_decisions_evaluated"] == 4
        assert summary["approved_committed"] == 1
        assert summary["overridden_committed"] == 1
        assert summary["total_committed"] == 2
        assert summary["skipped_existing_annotated"] == 1
        assert summary["skipped_deferred"] == 1

        # Check committed file content
        with open(test_annotator_file, encoding="utf-8") as f:
            records = [json.loads(line) for line in f]

        rec_map = {r["position_id"]: r for r in records}

        # pos-already-annotated is UNTOUCHED
        assert rec_map["pos-already-annotated"]["annotator_id"] == "ANNOTATOR_A"
        assert rec_map["pos-already-annotated"]["label"] == "IRRELEVANT"
        assert rec_map["pos-already-annotated"]["rationale"] == "Human annotated"

        # pos-to-approve is committed with AI provenance
        assert rec_map["pos-to-approve"]["annotation_status"] == "ANNOTATED"
        assert rec_map["pos-to-approve"]["annotator_id"] == "AI_ASSISTED_RESEARCHER_APPROVED"
        assert rec_map["pos-to-approve"]["label"] == "RELEVANT"
        assert rec_map["pos-to-approve"]["relevance_grade"] == 2

        # pos-to-override is committed with overridden label
        assert rec_map["pos-to-override"]["annotation_status"] == "ANNOTATED"
        assert rec_map["pos-to-override"]["label"] == "PARTIALLY_RELEVANT"
        assert rec_map["pos-to-override"]["relevance_grade"] == 1

        # pos-to-defer remained UNANNOTATED
        assert rec_map["pos-to-defer"]["annotation_status"] == "UNANNOTATED"

    def test_forbids_human_provenance_tag(self, test_annotator_file):
        rec_dummy = AIRecommendation(
            query_entities=[],
            requested_property=None,
            requested_relation=None,
            requested_outcome=None,
            entity_alignment=AlignmentType.NOT_APPLICABLE,
            relationship_alignment=AlignmentType.NOT_APPLICABLE,
            relationship_polarity=PolarityType.NOT_APPLICABLE,
            outcome_alignment=AlignmentType.NOT_APPLICABLE,
            outcome_polarity=PolarityType.NOT_APPLICABLE,
            evidence_claims=[],
            supported_claims=[],
            unsupported_claims=[],
            missing_information=[],
            counterevidence=[],
            uncertainties=[],
            best_supporting_span="",
            proposed_label=RelevanceLabel.IRRELEVANT,
            proposed_grade=0,
            proposed_rationale="",
            confidence=ConfidenceLevel.LOW,
            alternative_label_considered=None,
        )
        dec = ResearcherDecision(
            position_id="pos-to-approve",
            recommendation=rec_dummy,
            researcher_action=ResearcherAction.APPROVE,
        )
        with pytest.raises(ValueError, match="Invalid provenance tag"):
            commit_researcher_decisions([dec], test_annotator_file, provenance_tag="HUMAN")

        with pytest.raises(ValueError, match="Invalid provenance tag"):
            commit_researcher_decisions([dec], test_annotator_file, provenance_tag="ANNOTATOR_A")


# ==============================================================================
# 5. Tests for Engine Module
# ==============================================================================


class TestEngineModule:
    def test_engine_initialization_and_hashes(self):
        cfg = AnnotationSessionConfig(provider="mock")
        engine = AIAnnotationEngine(config=cfg, workspace_dir=WORKSPACE_ROOT)

        # Ensure prompts were loaded
        assert len(engine.system_prompt) > 0
        assert "{query}" in engine.adjudication_prompt_template
        assert "{evidence}" in engine.adjudication_prompt_template

        # Ensure hashes match frozen manifest
        assert "system_prompt_sha256" in engine.prompt_hashes
        assert "adjudication_prompt_sha256" in engine.prompt_hashes
        assert "challenge_prompt_sha256" in engine.prompt_hashes
        assert "track_a_adjudication_schema_sha256" in engine.prompt_hashes

    def test_engine_detects_prompt_tampering(self, tmp_path):
        # Create a tampered prompt
        tampered_prompt = tmp_path / "tampered_adjudication_prompt.txt"
        tampered_prompt.write_text("TAMPERED PROMPT {query} {evidence}", encoding="utf-8")

        cfg = AnnotationSessionConfig(
            provider="mock",
            adjudication_prompt_path=str(tampered_prompt),
            verify_prompt_hashes=True,
        )
        with pytest.raises(PromptHashMismatchError, match="Cryptographic hash mismatch"):
            AIAnnotationEngine(config=cfg, workspace_dir=WORKSPACE_ROOT)

    @pytest.mark.asyncio
    async def test_annotate_position_with_mock_backend(self):
        # Define mock callback that returns valid 21-field JSON
        mock_response = {
            "query_entities": ["lisinopril"],
            "requested_property": "clearance pathway",
            "requested_relation": None,
            "requested_outcome": None,
            "entity_alignment": "EXACT",
            "relationship_alignment": "EXACT",
            "relationship_polarity": "POSITIVE",
            "outcome_alignment": "NOT_APPLICABLE",
            "outcome_polarity": "NOT_APPLICABLE",
            "evidence_claims": [
                {
                    "claim_text": "Lisinopril is eliminated unchanged by renal excretion.",
                    "evidence_span": "eliminated unchanged by renal excretion",
                    "claim_type": "PHARMACOKINETIC",
                    "polarity": "POSITIVE",
                }
            ],
            "supported_claims": ["Lisinopril renal excretion."],
            "unsupported_claims": [],
            "missing_information": [],
            "counterevidence": [],
            "uncertainties": [],
            "best_supporting_span": "eliminated unchanged by renal excretion",
            "proposed_label": "RELEVANT",
            "proposed_grade": 2,
            "proposed_rationale": "Directly explains elimination mechanism.",
            "confidence": "HIGH",
            "alternative_label_considered": None,
        }

        cfg = AnnotationSessionConfig(provider="mock")
        engine = AIAnnotationEngine(
            config=cfg,
            llm_backend=lambda sys_p, usr_p, schema: mock_response,
            workspace_dir=WORKSPACE_ROOT,
        )

        pos = AnnotationPosition(
            position_id="pos-mock-01",
            query_id="q-01",
            query_text="Clearance pathway for lisinopril",
            chunk_id="c-01",
            document_id="d-01",
            retrieved_evidence="Lisinopril is eliminated unchanged by renal excretion.",
        )

        recommendation = await engine.annotate_position(pos)
        assert recommendation.proposed_label == RelevanceLabel.RELEVANT
        assert recommendation.proposed_grade == 2
        assert recommendation.best_supporting_span == "eliminated unchanged by renal excretion"

    @pytest.mark.asyncio
    async def test_annotate_batch_with_progress(self):
        mock_response = {
            "query_entities": [],
            "requested_property": None,
            "requested_relation": None,
            "requested_outcome": None,
            "entity_alignment": "MISMATCH",
            "relationship_alignment": "NOT_APPLICABLE",
            "relationship_polarity": "NOT_APPLICABLE",
            "outcome_alignment": "NOT_APPLICABLE",
            "outcome_polarity": "NOT_APPLICABLE",
            "evidence_claims": [],
            "supported_claims": [],
            "unsupported_claims": [],
            "missing_information": ["everything"],
            "counterevidence": [],
            "uncertainties": [],
            "best_supporting_span": "",
            "proposed_label": "IRRELEVANT",
            "proposed_grade": 0,
            "proposed_rationale": "Irrelevant text.",
            "confidence": "HIGH",
            "alternative_label_considered": None,
        }

        cfg = AnnotationSessionConfig(provider="mock")
        engine = AIAnnotationEngine(
            config=cfg,
            llm_backend=lambda sys_p, usr_p, schema: mock_response,
            workspace_dir=WORKSPACE_ROOT,
        )

        positions = [
            AnnotationPosition(
                position_id=f"pos-batch-{i}",
                query_id="q",
                query_text="q text",
                chunk_id=f"c-{i}",
                document_id=f"d-{i}",
                retrieved_evidence=f"evidence {i}",
            )
            for i in range(5)
        ]

        progress_updates = []

        def callback(done, total):
            progress_updates.append((done, total))

        results = await engine.annotate_batch(positions, batch_size=2, progress_callback=callback)
        assert len(results) == 5
        assert len(progress_updates) == 3  # Chunks: 2, 4, 5
        assert progress_updates[-1] == (5, 5)
