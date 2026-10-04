"""Live application Pydantic models for the multimodal Medical RAG.

These schemas serve the /api/v1/analyze endpoint and SSE streaming.
They are SEPARATE from the existing research/evaluation schemas.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


# ── Input Models ──────────────────────────────────────────────────────────────


class InputMode(str, Enum):
    prescription_image = "prescription_image"
    direct_drugs = "direct_drugs"
    multiple_drugs = "multiple_drugs"


class PatientContextInput(BaseModel):
    """Optional patient context — never inferred from prescriptions."""

    age: int | None = Field(default=None, ge=0, le=150)
    sex: str | None = Field(default=None, pattern=r"^(male|female|other)$")
    known_allergies: list[str] = Field(default_factory=list)
    known_conditions: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    pregnancy_status: str | None = Field(
        default=None, pattern=r"^(pregnant|not_pregnant|unknown)$"
    )
    breastfeeding: bool | None = None
    kidney_impairment: str | None = Field(
        default=None, pattern=r"^(none|mild|moderate|severe)$"
    )
    liver_impairment: str | None = Field(
        default=None, pattern=r"^(none|mild|moderate|severe)$"
    )

    @field_validator("known_allergies", "known_conditions", "current_medications")
    @classmethod
    def sanitize_lists(cls, v: list[str]) -> list[str]:
        """Strip whitespace and reject empty strings."""
        return [item.strip() for item in v if item.strip()]


class AnalyzeRequest(BaseModel):
    """POST /api/v1/analyze request body (JSON mode)."""

    input_mode: InputMode = InputMode.direct_drugs
    drug_names: list[str] = Field(
        default_factory=list,
        max_length=20,
        description="Drug names to analyze (max 20).",
    )
    patient_context: PatientContextInput | None = None

    @field_validator("drug_names")
    @classmethod
    def validate_drug_names(cls, v: list[str]) -> list[str]:
        """Strip, deduplicate, reject PHI patterns."""
        import re

        cleaned: list[str] = []
        seen: set[str] = set()
        phi_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",
            r"\bMRN\s*#?\s*\d+\b",
            r"\bDOB:\s*\d",
        ]
        for name in v:
            name = name.strip()
            if not name or len(name) < 2:
                continue
            for pat in phi_patterns:
                if re.search(pat, name, re.IGNORECASE):
                    raise ValueError("Drug name field contains PHI pattern.")
            lower = name.lower()
            if lower not in seen:
                seen.add(lower)
                cleaned.append(name)
        return cleaned


class ConfirmRequest(BaseModel):
    """POST /api/v1/confirm — confirm extracted medications after OCR."""

    request_id: str = Field(..., min_length=8, max_length=64)
    confirmed_medications: list[dict[str, Any]] = Field(default_factory=list)


# ── Output Models ─────────────────────────────────────────────────────────────


class MedicationResult(BaseModel):
    raw_text: str
    canonical_name: str | None = None
    rxcui: str | None = None
    brand_name: str | None = None
    formulation: str | None = None
    strength: str | None = None
    frequency: str | None = None
    route: str | None = None
    confidence: float = 0.0
    source: str = "unresolved"
    status: str = "UNAVAILABLE"


class DrugInteractionResult(BaseModel):
    drug_a: str
    drug_b: str
    rxcui_a: str = ""
    rxcui_b: str = ""
    interaction_detected: bool = False
    interaction_type: str | None = None
    potential_effect: str | None = None
    severity: str | None = None
    evidence_status: str = "NOT_ESTABLISHED"
    relationship_status: str = "UNAVAILABLE"
    sources: list[str] = Field(default_factory=list)


class AdverseDrugReactionResult(BaseModel):
    drug: str
    reaction: str
    severity: str = "common"
    evidence_level: str = "UNKNOWN"
    frequency: str | None = None
    source: str = ""


class FoodGuidanceResult(BaseModel):
    drug: str
    administration: str = ""
    food_relationship: str = "UNKNOWN"
    timing: str | None = None
    food_interactions: list[str] = Field(default_factory=list)
    evidence_status: str = "NOT_VERIFIED"
    source: str | None = None


class PatientConsiderationResult(BaseModel):
    factor: str
    provided: bool = False
    evidence_found: bool = False
    consideration: str = ""
    evidence_status: str = "UNKNOWN"
    source: str | None = None


class TrustFactorsResult(BaseModel):
    source_authority: float | None = None
    query_relevance: float | None = None
    evidence_quality: float | None = None
    freshness: float | None = None
    consistency: float | None = None
    entity_match: float | None = None
    population_match: float | None = None
    anti_poisoning: float | None = None
    anti_injection: float | None = None


class TrustResult(BaseModel):
    overall_score: float = 0.0
    threshold: float = 0.0
    risk_class: str = "R0"
    is_eligible: bool = False
    factors: TrustFactorsResult = Field(default_factory=TrustFactorsResult)
    missing_factors: list[str] = Field(default_factory=list)


class SecurityResult(BaseModel):
    injection_status: str = "ALLOW"
    poisoning_status: str = "ALLOW"
    injection_markers: list[str] = Field(default_factory=list)
    poisoning_reason: str | None = None


class ClaimResult(BaseModel):
    claim_id: int = 0
    text: str = ""
    support_state: str = "UNSUPPORTED"
    entailment: float = 0.0
    contradiction: float = 0.0
    citation_present: bool = False
    citation_resolves: bool = False
    best_evidence_chunk: str | None = None
    canonical_identity_status: str | None = None


class EvidenceResult(BaseModel):
    chunk_id: str = ""
    document_id: str = ""
    source_type: str = ""
    source_name: str = ""
    title: str = ""
    text: str = ""
    pmid: str | None = None
    doi: str | None = None
    url: str | None = None
    source_authority: float = 0.0
    trust_score: float = 0.0
    freshness: float = 0.0
    retrieval_method: str = ""
    provenance_status: str = ""


class ProvenanceStep(BaseModel):
    level: str
    id: str
    label: str
    detail: str | None = None


class AnalyzeResponse(BaseModel):
    """Final structured analysis response."""

    request_id: str
    input_mode: str
    processing_time_ms: float = 0.0

    medications: list[MedicationResult] = Field(default_factory=list)
    patient_context_used: PatientContextInput | None = None

    interactions: list[DrugInteractionResult] = Field(default_factory=list)
    adverse_reactions: list[AdverseDrugReactionResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    food_guidance: list[FoodGuidanceResult] = Field(default_factory=list)
    patient_considerations: list[PatientConsiderationResult] = Field(
        default_factory=list
    )

    trust: TrustResult | None = None
    security: SecurityResult | None = None
    claims: list[ClaimResult] = Field(default_factory=list)
    evidence: list[EvidenceResult] = Field(default_factory=list)
    provenance: list[ProvenanceStep] = Field(default_factory=list)

    conclusion: str | None = None
    gate_decision: str = "abstain"
    abstention_reason: str | None = None

    disclaimer: str = (
        "RESEARCH OUTPUT ONLY. Not reviewed by clinicians. "
        "Not for clinical use. Evidence-grounded response from a research testbed."
    )


class AnalyzeAccepted(BaseModel):
    """Response when analysis request is accepted for SSE streaming."""

    request_id: str
    stream_url: str
