# EXECUTION PATH

1. **QUERY**: Input received via `RAGRequest`.
2. **RETRIEVAL**: Hybrid search fetches candidates.
3. **TRUST SCORING**: `AdaptiveTrustScorer` applies R0-R3 thresholds.
4. **EVIDENCE FILTERING**: `EvidenceEligibilityGate` drops untrusted or low-authority chunks.
5. **PRE-GEN ABSTENTION**: If 0 chunks remain, orchestrator calls `_abstain()`. Generation is SKIPPED.
6. **GENERATION**: LLM generates grounded answer.
7. **CLAIM EXTRACTION**: Output split into atomic claims.
8. **CLAIM-EVIDENCE VERIFICATION**: `ClaimVerifierV2` validates semantic entailment and citations.
9. **POST-GEN ABSTENTION**: `AnswerSafetyGate` checks grounding ratio. If failed, returns `GateDecision.abstain`. Orchestrator calls `_abstain()`.
10. **FINAL OUTPUT**: Valid answers are formatted with RESEARCH_DISCLAIMER. Abstained answers emit a safe fallback template.
