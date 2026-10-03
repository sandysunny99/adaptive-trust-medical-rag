# TRUST P0 V2 DOWNSTREAM NONE AUDIT

- `TrustFactorScores` allows `float | None`.
- `TrustScoringResult` strictly outputs `trust_score: float`.
- Downstream orchestration (`rag_orchestrator.py`) handles `trust_score` numerically. It does not perform arithmetic on `None`. Incomplete evidence yields a lower `trust_score`, which is correctly rejected by threshold logic.
- Result: None is safe downstream.
