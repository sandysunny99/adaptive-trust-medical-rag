# TRUST P0 REMEDIATION IMPLEMENTATION REPORT V1

- **Files Changed:** `src/adaptive_trust_medical_rag/trust_scoring/trust_scorer.py`, `tests/test_trust_scorer.py`
- **Fields Changed:** All 9 fields in `TrustFactorScores` converted from `float = X` to `float | None = None`.
- **Call Sites Changed:** No production call sites changed. Existing code naturally passes `None` by omitting arguments.
- **Old Behavior:** `total = sum(weight * val)` using silent imputed defaults.
- **New Behavior:** `missing_factors` collected. `total = sum(weight * val)` for non-None. `trust_score = total / weight_sum`.
- **Serialization Behavior:** `as_dict()` modified to permit `float | None`.
- **Regression Tests:** 2 explicit tests added to compare explicit numeric against explicitly missing state. 38/38 tests pass.
