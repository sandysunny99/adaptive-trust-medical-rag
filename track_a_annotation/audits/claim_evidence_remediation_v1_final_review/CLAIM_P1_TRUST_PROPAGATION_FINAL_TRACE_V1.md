# P1 TRUST PROPAGATION FINAL TRACE
- `rag_orchestrator.py` Step 5 computes `TrustScoringResult`.
- Both `trust_score` and `missing_factors` are stored.
- `rag_orchestrator.py` Step 8 instantiates `EvidenceChunk` with these fields.
- `ClaimVerifierV2.verify` reads these from `EvidenceChunk` and aggregates them into `SemanticJudgment`.
