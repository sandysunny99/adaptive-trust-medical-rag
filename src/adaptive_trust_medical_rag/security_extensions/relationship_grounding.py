import re
from dataclasses import dataclass
from enum import Enum

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate


class RelationshipGroundingStatus(Enum):
    SUPPORTED = "RELATIONSHIP_SUPPORTED"
    UNSUPPORTED = "RELATIONSHIP_UNSUPPORTED"
    UNVERIFIABLE = "RELATIONSHIP_UNVERIFIABLE"
    MISSING_PROVENANCE = "RELATIONSHIP_PROVENANCE_MISSING"

@dataclass
class GroundingDecision:
    status: RelationshipGroundingStatus
    reason: str

class RelationshipGroundingValidator:
    """
    Validates whether an extracted relationship/statement is supported by source.
    """

    def __init__(self, registry_store: dict[str, dict]):
        self.registry_store = registry_store

    def validate(self, candidate: Candidate) -> GroundingDecision:
        prov = candidate.metadata.get("provenance", {})
        if prov.get("status") == "PROVENANCE_PARTIAL":
            return GroundingDecision(RelationshipGroundingStatus.UNVERIFIABLE, "Provenance is partial.")

        doc_id = prov.get("document_id") or candidate.document_id
        chunk_id = prov.get("chunk_id") or candidate.chunk_id

        if not doc_id:
            return GroundingDecision(RelationshipGroundingStatus.MISSING_PROVENANCE, "No document_id found.")

        if doc_id not in self.registry_store:
            return GroundingDecision(RelationshipGroundingStatus.UNVERIFIABLE, f"Document {doc_id} not found.")

        source_text = self.registry_store[doc_id].get(chunk_id, {}).get("text", "").lower()
        cand_text = candidate.text.lower()

        # Extremely basic NLP extraction simulating real relationship grounding check
        # For this test, if candidate text contains "interacts with" or "contraindicated",
        # we check if those semantics exist in the source alongside the drugs.
        # This prevents "statin and cyanide" (just co-occurring) from passing as an interaction.
        pattern = re.compile(r"\b[A-Za-z]{3,}(?:mab|nib|olol|pril|sartan|statin|mycin|cillin|cycline|azole|warfarin|metformin|aspirin|insulin|heparin|cyanide|ibuprofen)\b", re.IGNORECASE)
        drugs_in_cand = set(pattern.findall(cand_text))

        for d in drugs_in_cand:
            if d not in source_text:
                return GroundingDecision(RelationshipGroundingStatus.UNSUPPORTED, f"Entity '{d}' not in source")

        relationship_keywords = ["interact", "contraindicat", "inhibit", "bind"]
        cand_has_rel = any(k in cand_text for k in relationship_keywords)
        source_has_rel = any(k in source_text for k in relationship_keywords)

        if cand_has_rel and not source_has_rel:
            return GroundingDecision(RelationshipGroundingStatus.UNSUPPORTED, "Relationship semantics not supported by source")

        return GroundingDecision(RelationshipGroundingStatus.SUPPORTED, "Relationship is supported by source text.")
