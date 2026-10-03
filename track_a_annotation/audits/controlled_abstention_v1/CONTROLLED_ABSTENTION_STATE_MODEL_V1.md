# ABSTENTION STATE MODEL

The system uses three tiers of state:

1. **Atomic Claim State**:
   - `SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`.
2. **Gate Decision**:
   - `QUALIFY`: Minor claims unsupported; answer emitted with a warning prefix.
   - `ABSTAIN`: Critical failure; answer dropped.
   - `RELEASE`: Full pass.
3. **Orchestrator Final State**:
   - `RAGResponse(abstained=True, abstention_reason="...")`
   - `RAGResponse(abstained=False, answer="...")`
