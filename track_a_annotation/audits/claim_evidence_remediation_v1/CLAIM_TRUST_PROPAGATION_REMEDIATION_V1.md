# TRUST PROPAGATION REMEDIATION
- Fixed CEA-P1-002.
- `rag_orchestrator.py` modified to capture `missing_factors` during adaptive trust scoring (Step 5).
- `EvidenceChunk` and `SemanticJudgment` extended to carry `trust_score` and `missing_factors`.
- `ClaimVerifierV2` exposes this metadata to downstream consumers.
