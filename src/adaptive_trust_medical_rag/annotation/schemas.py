"""Data models for AI-assisted medical evidence annotation.

Matches Schema V2 and the Track A adjudication specification.
Enforces strict provenance, label-grade consistency, and reproducible hashing.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ==============================================================================
# Enumerations
# ==============================================================================


class RelevanceLabel(str, Enum):
    """Relevance labels conforming to Track A Schema V2."""

    RELEVANT = "RELEVANT"
    PARTIALLY_RELEVANT = "PARTIALLY_RELEVANT"
    IRRELEVANT = "IRRELEVANT"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"
    AMBIGUOUS = "AMBIGUOUS"


LABEL_TO_GRADE_MAP: dict[str, Optional[int]] = {
    RelevanceLabel.RELEVANT.value: 2,
    RelevanceLabel.PARTIALLY_RELEVANT.value: 1,
    RelevanceLabel.IRRELEVANT.value: 0,
    RelevanceLabel.INSUFFICIENT_INFORMATION.value: 0,
    RelevanceLabel.AMBIGUOUS.value: None,
}


class AlignmentType(str, Enum):
    """Alignment between queried and evidence concepts."""

    EXACT = "EXACT"
    PARTIAL = "PARTIAL"
    MISMATCH = "MISMATCH"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class PolarityType(str, Enum):
    """Relationship / outcome polarity."""

    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    UNCERTAIN = "UNCERTAIN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ClaimPolarity(str, Enum):
    """Polarity of extracted evidence claims."""

    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    UNCERTAIN = "UNCERTAIN"


class ClaimType(str, Enum):
    """Domain categorization for evidence claims."""

    PHARMACOKINETIC = "PHARMACOKINETIC"
    PHARMACODYNAMIC = "PHARMACODYNAMIC"
    CLINICAL_OUTCOME = "CLINICAL_OUTCOME"
    MECHANISM = "MECHANISM"
    ADVERSE_EVENT = "ADVERSE_EVENT"
    OTHER = "OTHER"


class ConfidenceLevel(str, Enum):
    """Confidence level assigned by the adjudicator."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ResearcherAction(str, Enum):
    """Action taken by the human researcher on an AI recommendation."""

    APPROVE = "APPROVE"
    OVERRIDE = "OVERRIDE"
    DEFER = "DEFER"
    REJECT = "REJECT"


class AnnotationState(str, Enum):
    """Lifecycle state of an annotation position."""

    UNANNOTATED = "UNANNOTATED"
    IN_PROGRESS = "IN_PROGRESS"
    ANNOTATED = "ANNOTATED"
    QA_FLAGGED = "QA_FLAGGED"
    QA_RESOLVED = "QA_RESOLVED"
    FROZEN = "FROZEN"


# ==============================================================================
# Core Models
# ==============================================================================


class EvidenceClaim(BaseModel):
    """Explicit claim extracted from the retrieved text with exact span grounding."""

    model_config = ConfigDict(extra="forbid")

    claim_text: str = Field(description="Normalized claim statement.")
    evidence_span: str = Field(description="Exact contiguous substring from retrieved text.")
    claim_type: ClaimType = Field(description="Domain categorization.")
    polarity: ClaimPolarity = Field(description="Claim polarity.")


class AnnotationPosition(BaseModel):
    """Represents a retrieval position to be evaluated in Track A."""

    model_config = ConfigDict(extra="allow")

    position_id: str
    query_id: str
    query_text: str
    chunk_id: str
    document_id: str
    retrieved_evidence: str
    original_evidence_available: bool = True
    abstract_available: bool = True
    abstract_enrichment_status: Optional[str] = None
    annotator_id: Optional[str] = None
    relevance_grade: Optional[int] = None
    grade: Optional[int] = None
    label: Optional[str] = None
    rationale: Optional[str] = None
    evidence_span: Optional[str] = None
    timestamp: Optional[str] = None
    schema_version: str = "2.0.0"
    annotation_status: str = "UNANNOTATED"
    human_confirmation: Optional[bool] = None
    llm_assistance: Optional[str] = None


class AIRecommendation(BaseModel):
    """Strict 21-field structured adjudication recommendation from the LLM."""

    model_config = ConfigDict(extra="allow")

    query_entities: list[str] = Field(default_factory=list)
    requested_property: Optional[str] = None
    requested_relation: Optional[str] = None
    requested_outcome: Optional[str] = None
    entity_alignment: AlignmentType
    relationship_alignment: AlignmentType
    relationship_polarity: PolarityType
    outcome_alignment: AlignmentType
    outcome_polarity: PolarityType
    evidence_claims: list[EvidenceClaim] = Field(default_factory=list)
    supported_claims: list[str] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    counterevidence: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    best_supporting_span: str = ""
    proposed_label: RelevanceLabel
    proposed_grade: Optional[int] = None
    proposed_rationale: str
    confidence: ConfidenceLevel
    alternative_label_considered: Optional[RelevanceLabel] = None

    @model_validator(mode="after")
    def validate_label_grade_consistency(self) -> AIRecommendation:
        label_val = (
            self.proposed_label.value
            if isinstance(self.proposed_label, RelevanceLabel)
            else self.proposed_label
        )
        expected_grade = LABEL_TO_GRADE_MAP.get(label_val)
        if self.proposed_grade != expected_grade:
            raise ValueError(
                f"Proposed grade {self.proposed_grade} is inconsistent with label '{label_val}'. "
                f"Expected grade: {expected_grade}"
            )
        return self

    def validate_spans(self, evidence_text: str) -> list[str]:
        """Validate that all spans exist contiguously in the evidence text."""
        errors: list[str] = []
        label_val = (
            self.proposed_label.value
            if isinstance(self.proposed_label, RelevanceLabel)
            else self.proposed_label
        )

        if label_val in (RelevanceLabel.RELEVANT.value, RelevanceLabel.PARTIALLY_RELEVANT.value):
            if not self.best_supporting_span.strip():
                errors.append(f"best_supporting_span is required for {label_val} but is empty.")
            elif self.best_supporting_span not in evidence_text:
                errors.append(
                    f"best_supporting_span is not a contiguous substring of evidence: '{self.best_supporting_span[:60]}...'"
                )
        elif self.best_supporting_span and self.best_supporting_span not in evidence_text:
            errors.append(
                f"best_supporting_span is not a contiguous substring of evidence: '{self.best_supporting_span[:60]}...'"
            )

        for i, claim in enumerate(self.evidence_claims):
            if claim.evidence_span and claim.evidence_span not in evidence_text:
                errors.append(
                    f"evidence_claim[{i}] span is not a contiguous substring of evidence: '{claim.evidence_span[:60]}...'"
                )

        return errors


class ResearcherDecision(BaseModel):
    """Wraps an AI recommendation with human researcher adjudication decisions."""

    model_config = ConfigDict(extra="allow")

    position_id: str
    recommendation: AIRecommendation
    researcher_action: ResearcherAction
    researcher_rationale: Optional[str] = None
    final_label: Optional[RelevanceLabel] = None
    final_grade: Optional[int] = None
    final_evidence_span: Optional[str] = None
    decision_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    researcher_id: Optional[str] = None

    @model_validator(mode="after")
    def populate_and_validate_decision(self) -> ResearcherDecision:
        action = self.researcher_action

        if action == ResearcherAction.APPROVE:
            if self.final_label is None:
                self.final_label = self.recommendation.proposed_label
            if self.final_grade is None:
                self.final_grade = self.recommendation.proposed_grade
            if self.final_evidence_span is None:
                self.final_evidence_span = self.recommendation.best_supporting_span
            if not self.researcher_rationale:
                self.researcher_rationale = (
                    f"Approved AI recommendation ({self.final_label.value}): "
                    f"{self.recommendation.proposed_rationale}"
                )
        elif action == ResearcherAction.OVERRIDE:
            if self.final_label is None:
                raise ValueError("OVERRIDE action requires explicit final_label.")
            if self.final_grade is None:
                lbl_val = (
                    self.final_label.value
                    if isinstance(self.final_label, RelevanceLabel)
                    else self.final_label
                )
                self.final_grade = LABEL_TO_GRADE_MAP.get(lbl_val)
            if not self.researcher_rationale:
                raise ValueError(
                    "OVERRIDE action requires researcher_rationale explaining the override."
                )
        elif action in (ResearcherAction.DEFER, ResearcherAction.REJECT):
            # For defer / reject, final_label may remain None or reflect deferred status
            pass

        if self.final_label is not None:
            lbl_val = (
                self.final_label.value
                if isinstance(self.final_label, RelevanceLabel)
                else self.final_label
            )
            expected = LABEL_TO_GRADE_MAP.get(lbl_val)
            if self.final_grade != expected:
                raise ValueError(
                    f"Final grade {self.final_grade} is inconsistent with final_label '{lbl_val}'. Expected: {expected}"
                )

        return self


class AnnotationSessionConfig(BaseModel):
    """Configuration for LLM-assisted annotation execution."""

    model_config = ConfigDict(extra="allow")

    provider: str = "groq"
    model: str = "openai/gpt-oss-120b"
    temperature: float = 0.0
    top_p: float = 0.1
    max_tokens: int = 2048
    seed: Optional[int] = 42
    timeout_seconds: float = 120.0
    structured_output_method: str = "JSON_OBJECT"
    system_prompt_path: Optional[str] = None
    adjudication_prompt_path: Optional[str] = None
    challenge_prompt_path: Optional[str] = None
    schema_path: Optional[str] = None
    verify_prompt_hashes: bool = True
    provenance_tag: str = "AI_ASSISTED_V1"

    def compute_config_hash(self) -> str:
        """Deterministic SHA256 of execution parameters."""
        canonical_dict = {
            "provider": self.provider,
            "model": self.model,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "seed": self.seed,
            "structured_output_method": self.structured_output_method,
            "provenance_tag": self.provenance_tag,
        }
        serialized = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class AnnotationBatch(BaseModel):
    """Metadata and contents of an annotation processing batch."""

    model_config = ConfigDict(extra="allow")

    batch_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    positions: list[AnnotationPosition] = Field(default_factory=list)
    config_hash: str
    prompt_hashes: dict[str, str] = Field(default_factory=dict)
    recommendations: list[AIRecommendation] = Field(default_factory=list)
    status: str = "PENDING"
    model_metadata: dict[str, Any] = Field(default_factory=dict)
