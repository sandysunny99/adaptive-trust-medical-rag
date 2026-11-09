# TRUST HISTORICAL IMPACT (GATE 5)

**Date:** 2026-10-03  
**Stage:** GATE B (Architecture Freeze)  
**Classification:** MODERATE IMPACT / REQUIRES_RERUN_IF_CHANGED

## 1. Actual Gate 5 State

During the frozen Gate 5 execution, the `AdaptiveTrustScorer` operated with the following exact inputs for all evidence candidates:
- `query_relevance`: **0.0** (Missing)
- `evidence_quality`: **0.0** (Missing)
- `population_match`: **1.0** (Defaulted)

## 2. Mathematical Impact on Gate 5 Scores

The missing values caused a systematic depression of all recorded trust scores.
- **R0 Queries:** Score depressed by -0.30. Max achieved = 0.70.
- **R1 Queries:** Score depressed by -0.35. Max achieved = 0.65.
- **R2 Queries:** Score depressed by -0.35. Max achieved = 0.65.
- **R3 Queries:** Score depressed by -0.35. Max achieved = 0.65.

## 3. Did it affect eligibility?

- **R0, R1, R2:** These thresholds (0.30, 0.45, 0.60) remained mathematically reachable. Highly authoritative candidates (e.g., RxNorm, PubMed) could pass the R1 and R2 gates despite the 35% penalty, provided their other factors (freshness, entity match) were near perfect.
- **R3:** The threshold (0.75) was mathematically impossible. If any R3 queries were present in Gate 5, their evidence was unconditionally rejected, triggering controlled abstention.

## 4. Methodological Conclusion

If the Trust Missing-Value Policy is changed (Option A or Option B), the absolute trust scores will shift upward or be renormalized. 
- **Effect:** Any future experiment's trust distribution will be mathematically incomparable to the Gate 5 frozen distribution. 
- **Required Action:** If Option A or B is selected, the baseline portion of Gate 5 **must be rerun** to establish a valid comparative baseline for the new metric definition before evaluating Cognee. If Option C is selected, Gate 5 is perfectly preserved.
