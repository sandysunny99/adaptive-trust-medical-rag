"""Staged Evidence Query Router

Project: Adaptive Trust-Aware Medical RAG
Component: EvidenceQueryRouter

Routes medical queries by risk tier and claim type to P0/P1 sources and calculates
claim-source compatibility (claim_source_fit) scores.
"""

from __future__ import annotations

from typing import Any


class EvidenceQueryRouter:
    """Routes medical queries to appropriate external evidence providers based on claim fit."""

    CLAIM_SOURCE_FIT_MATRIX: dict[str, str] = {
        "drug_normalization": "rxnorm",
        "fda_labeling": "openfda",
        "trial_status": "clinicaltrials",
        "research_evidence": "pubmed",
        "metadata_verification": "crossref",
        "citation_network": "europepmc",
    }

    def route_query(
        self, query: str, risk_tier: str = "R1", claim_type: str | None = None
    ) -> dict[str, Any]:
        """Select appropriate evidence providers and compute source priorities."""
        q_lower = query.lower()
        selected_sources = ["pubmed", "europepmc"]
        preferred_fit = "research_evidence"

        if "adverse" in q_lower or "warning" in q_lower or "label" in q_lower or risk_tier == "R3":
            selected_sources = ["openfda", "pubmed", "europepmc"]
            preferred_fit = "fda_labeling"
        elif "trial" in q_lower or "study design" in q_lower or "recruitment" in q_lower:
            selected_sources = ["pubmed", "europepmc"]
            preferred_fit = "trial_status"
        elif "mechanism" in q_lower or "dose" in q_lower or "indication" in q_lower:
            selected_sources = ["rxnorm", "pubmed", "europepmc"]
            preferred_fit = "research_evidence"

        if claim_type and claim_type in self.CLAIM_SOURCE_FIT_MATRIX:
            preferred_fit = claim_type
            primary_src = self.CLAIM_SOURCE_FIT_MATRIX[claim_type]
            if primary_src not in selected_sources:
                selected_sources.insert(0, primary_src)

        return {
            "query": query,
            "risk_tier": risk_tier,
            "selected_sources": selected_sources,
            "preferred_claim_fit": preferred_fit,
            "required_quorum": 2 if risk_tier in ("R2", "R3") else 1,
        }

    def calculate_claim_source_fit(self, source_type: str, claim_type: str) -> float:
        """Compute numerical claim_source_fit score in [0.0, 1.0]."""
        if claim_type == "fda_labeling" and source_type == "PRIMARY_REGULATORY":
            return 1.0
        if claim_type == "drug_normalization" and source_type == "ENTITY_TERMINOLOGY":
            return 1.0
        if claim_type == "research_evidence" and source_type == "BIOMEDICAL_LITERATURE":
            return 1.0
        if claim_type == "trial_status" and source_type == "PRIMARY_CLINICAL_REGISTRY":
            return 1.0
        return 0.70
