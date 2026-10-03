# RELATIONSHIP SCOPE REMEDIATION
- Fixed CEA-P1-003.
- `EvidenceChunk` now includes `relationship_scope`.
- `rag_orchestrator.py` passes the RG-02 status to `EvidenceChunk`.
- `ClaimVerifierV2` overrides `state = UNSUPPORTED` if the cited chunk's scope is `NO_RELEVANT_RELATION` or other unauthorized states.
