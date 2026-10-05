from typing import Any

from adaptive_trust_medical_rag.security.security_context import SecurityDecision, SecurityState


class RetrievalPoisoningDetector:
    """Detects suspicious source/document metadata patterns indicating poisoning."""

    def __init__(self):
        # Lightweight heuristic blocklist
        self.suspicious_sources = {"unverified_blog", "anonymized_pastebin", "hacked_db"}

    def inspect_provenance(self, provenance: dict[str, Any], chunk_id: str, request_id: str) -> SecurityDecision:
        if not provenance:
            return SecurityDecision(
                decision=SecurityState.BLOCK,
                reason_code="MISSING_PROVENANCE",
                attack_family="RETRIEVAL_POISONING",
                attack_subtype="PROVENANCE_MISSING",
                confidence=1.0,
                target="retriever",
                source=chunk_id,
                evidence_id=chunk_id,
                request_id=request_id,
                detector="RetrievalPoisoningDetector"
            )

        source = str(provenance.get("source", "")).lower()
        if source in self.suspicious_sources:
            return SecurityDecision(
                decision=SecurityState.BLOCK,
                reason_code="SUSPICIOUS_SOURCE",
                attack_family="RETRIEVAL_POISONING",
                attack_subtype="PROVENANCE_BLACKLISTED",
                confidence=1.0,
                target="retriever",
                source=chunk_id,
                evidence_id=chunk_id,
                request_id=request_id,
                detector="RetrievalPoisoningDetector",
                provenance_reference=source
            )

        # Missing identity for a known trusted authority
        if source == "pubmed" and not provenance.get("document_id"):
            return SecurityDecision(
                decision=SecurityState.BLOCK,
                reason_code="MISSING_ID",
                attack_family="RETRIEVAL_POISONING",
                attack_subtype="PROVENANCE_INCOMPLETE",
                confidence=1.0,
                target="retriever",
                source=chunk_id,
                evidence_id=chunk_id,
                request_id=request_id,
                detector="RetrievalPoisoningDetector",
                provenance_reference=source
            )

        return SecurityDecision(
            decision=SecurityState.ALLOW,
            reason_code="PROVENANCE_SAFE",
            attack_family="RETRIEVAL_POISONING",
            confidence=1.0,
            target="retriever",
            source=chunk_id,
            evidence_id=chunk_id,
            request_id=request_id,
            detector="RetrievalPoisoningDetector",
            provenance_reference=source
        )
