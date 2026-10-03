# TRUST P0 DOWNSTREAM CONSUMER MATRIX V1

| Consumer | File | Field | Current Behavior | Missing Input Possible? | Mathematical Use | Gate/Decision Effect |
|---|---|---|---|---|---|---|
| `AdaptiveTrustScorer` | `trust_scorer.py` | All | Excludes missing | YES | Numerator/denominator exclusion | Rescores proportionately |
| `TrustScoringResult` | `trust_scorer.py` | `missing_factors` | Logs missing | YES | None | Audit visibility |
| `rag_orchestrator.py` | `rag_orchestrator.py` | `trust_score` | Threshold check | NO | Float comparison | Abstains if < threshold |
| `ClaimVerifierV2` | `claim_verifier_v2.py` | `trust_score` | N/A | NO | None | None |
