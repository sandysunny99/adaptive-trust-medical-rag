# GATE B HUMAN DECISION PACKAGE V4

**Date:** 2026-10-03  

## 1. What is definitely known
- The current implementation defaults `query_relevance` and `evidence_quality` to `0.0`.
- The current implementation sets `anti_injection` to a constant `1.0`.
- The normative protocol is silent on missing-value fallback rules and ambiguous on whether `anti_injection` should be continuous or a hard gate.

## 2. What is mathematically proven
- Maximum achievable scores currently: R0(0.70), R1-R3(0.65).
- R3 Threshold (0.75) is mathematically impassable.
- The historical Gate 5 `anti_injection` evaluation (`1.0 - 0.0`) is numerically identical to the current constant (`1.0`).

## 3. What actually happened in Gate 5
- Gate 5 tested frozen R1/R2 baseline queries.
- **R3_HISTORICAL_IMPACT_UNVERIFIED**: Without a manual audit of all baseline logs, there is no definitive proof that R3 cases were present. If they were absent, the 0.65 trust ceiling caused zero actual rejections.

## 4. What remains unknown
- Whether any R3 cases were genuinely present in the offline baseline.

## 5. Trust Policy A1 (Direct Retrieval Imputation)
- Imputes missing variables using BM25/Cosine scores. Creates severe circularity and confounds the Baseline vs Cognee experiment. Forces Gate 5 rerun.

## 6. Trust Policy A2 (Independent Relevance)
- Uses cross-encoder or LLM-judge. Avoids circularity but requires building new modules. Does not solve `evidence_quality` missing values. Forces Gate 5 rerun.

## 7. Trust Policy B (Renormalize)
- Converts to 7-factor model. Shifts weight massively to `authority`. Forces Gate 5 rerun.

## 8. Trust Policy C (Keep Missing=Zero)
- Preserves the existing missing=zero implementation and produces conservative score behavior, but its normative safety rationale is not explicitly specified by the current protocol. Numerical delta: 0.0.

## 9. Anti-Injection A (Constant 1.0)
- Preserves historical denominator perfectly. Semantically acts as a zero-value placeholder since the hard gate provides the actual security. Numerical delta: 0.0.

## 10. Anti-Injection B (Hard Gate Only)
- Cleans up semantics by removing the constant from continuous trust. Alters denominator. Forces Gate 5 rerun.

## 11. Anti-Injection C (New Continuous Signal)
- Requires building a continuous probability injection detector. Forces Gate 5 rerun.

## 12. Historical rerun implications
- Option C + Option A is the only combination with a numerical delta of 0.0, avoiding a rerun. Any other combination forces a full 92-run regeneration.

## 13. Methodology implications
- Missing values currently operate as a measurement limitation, not an intentionally designed protocol.

## 14. Benchmark implications
- Option A1 explicitly invalidates the benchmark comparability.

## 15. Human decisions required
- Select Trust Missing-Value Policy.
- Select Anti-Injection Representation.
