# TRUST P0 MISSING DATA BEHAVIOR V1

The lifecycle of omitted trust dimensions:
1. **RAW INPUT**: Factor is omitted at the constructor (e.g., `TrustFactorScores(source_authority=0.8)`).
2. **TrustFactorScores**: Dataclass fills missing fields with numeric defaults (`0.0` or `1.0`).
3. **TRUST SCORE CALCULATION**: The default numbers are multiplied by risk weights.
4. **THRESHOLD/GATE**: The resulting aggregated float is compared against the threshold.
5. **DOWNSTREAM DECISION**: A chunk may be silently rejected (because `evidence_quality` = 0.0) or silently accepted (because `population_match` = 1.0) without indicating uncertainty.

**Conclusion**: Missing data collapses into ZERO or ONE. There is no representation of `MISSING`, `UNKNOWN`, or `NULL`.
