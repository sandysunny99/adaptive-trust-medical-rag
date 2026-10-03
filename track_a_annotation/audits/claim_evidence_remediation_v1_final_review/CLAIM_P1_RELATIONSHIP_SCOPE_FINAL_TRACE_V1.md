# P1 RELATIONSHIP SCOPE FINAL TRACE
- `rag_orchestrator.py` queries `grounding_states[chunk_id].status.name`.
- Passes this string to `EvidenceChunk.relationship_scope`.
- `ClaimVerifierV2.verify` extracts `claim_relationship_scope` from the cited chunks.
- If scope in `("NO_RELEVANT_RELATION", "UNSUPPORTED", "CONTRADICTED", "ENTITY_PAIR_MISMATCH", "UNVERIFIABLE")`, sets `UNSUPPORTED`.
