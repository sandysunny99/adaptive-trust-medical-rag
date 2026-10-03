# PRODUCTION SCOPE AUDIT
- Modifies `claim_verifier_v2.py`.
- Modifies `rag_orchestrator.py`.
- Modifies `claim_verifier.py` (legacy verifier) **EXPLANATION**: Added metadata fields to `EvidenceChunk` dataclass so that `rag_orchestrator.py` does not throw an initialization `TypeError` during standard execution flow. This was strictly an interface-alignment change.
