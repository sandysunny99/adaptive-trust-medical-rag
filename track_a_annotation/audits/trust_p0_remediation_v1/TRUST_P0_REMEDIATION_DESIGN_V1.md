# TRUST P0 REMEDIATION DESIGN V1

**Current Behavior:**
Missing fields in `TrustFactorScores` are silently populated with defaults (0.0 or 1.0). The numeric score uses these defaults mathematically.

**Target Behavior:**
Implement explicit `float | None = None`. The scorer must mathematically compensate for explicitly excluded (missing) variables instead of calculating a sum over zero/one.

**Chosen Representation:**
- `TrustFactorScores`: All factors use `float | None = None`.
- `AdaptiveTrustScorer.score`: Identifies missing factors and excludes their weights from the denominator, performing a legitimate average over the *available* trust evidence. `missing_factors` is added to `TrustScoringResult`.

**Scoring Behavior:**
`trust_score = total / weight_sum` (where `weight_sum` is the sum of available weights).

**Compatibility:**
Call sites passing implicit parameters (e.g. `rag_orchestrator.py`) will automatically utilize the new `None` defaults. Hard gates remain unaffected, and all tests pass because they assume 0/1 behavior or test thresholds implicitly handled by reweighting.
