import hashlib
from dataclasses import dataclass
from enum import Enum

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate


class IntegrityStatus(Enum):
    VERIFIED = "INTEGRITY_VERIFIED"
    MISMATCH = "INTEGRITY_MISMATCH"
    MISSING = "INTEGRITY_MISSING"

@dataclass
class IntegrityDecision:
    status: IntegrityStatus
    reason: str

class DynamicIntegrityValidator:
    """
    Validates dynamic content-hash integrity against a mock SourceRegistry.
    """

    def __init__(self, registry_store: dict[str, dict]):
        self.registry_store = registry_store

    def validate(self, candidate: Candidate) -> IntegrityDecision:
        prov = candidate.metadata.get("provenance", {})
        if prov.get("status") == "PROVENANCE_PARTIAL":
            return IntegrityDecision(IntegrityStatus.MISSING, "Provenance is partial; cannot verify integrity.")

        doc_id = prov.get("document_id") or candidate.document_id
        chunk_id = prov.get("chunk_id") or candidate.chunk_id

        if not doc_id or not chunk_id:
            return IntegrityDecision(IntegrityStatus.MISSING, "Missing document_id or chunk_id.")

        if doc_id not in self.registry_store:
            return IntegrityDecision(IntegrityStatus.MISSING, f"Document {doc_id} not found in registry.")

        expected_hash = self.registry_store[doc_id].get(chunk_id, {}).get("content_hash")
        if not expected_hash:
            return IntegrityDecision(IntegrityStatus.MISSING, "No expected hash in registry.")

        actual_hash = hashlib.sha256(candidate.text.encode('utf-8')).hexdigest()

        if actual_hash != expected_hash:
            return IntegrityDecision(IntegrityStatus.MISMATCH, f"Hash mismatch. Expected {expected_hash}, got {actual_hash}")

        return IntegrityDecision(IntegrityStatus.VERIFIED, "Content hash verified.")
