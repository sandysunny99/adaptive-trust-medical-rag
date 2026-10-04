# GATE B FINAL COUNTERFACTUAL DECISION PACKAGE V1

**Date:** 2026-10-03  
**Stage:** GATE B (Architecture Freeze)

## 1. VERIFIED CURRENT SYSTEM
- **Maximum Scores:** R0 (0.70), R1 (0.65), R2 (0.65), R3 (0.65).
- **Thresholds:** R0 (0.30), R1 (0.45), R2 (0.60), R3 (0.75).
- **Missing Values:** `query_relevance` and `evidence_quality` default to `0.0`.
- **Anti-Injection:** Currently set to `1.0`.

## 2. HISTORICAL RISK-TIER RESULTS
- **R0 / R1 / R2 Cases:** Present in Gate 5. Scores were depressed by 30-35%, but highly authoritative candidates successfully cleared the 0.30/0.45/0.60 thresholds.
- **R3 Cases:** Based on the standard pharmacological queries (DDI/ADE) used in the offline baseline, **R3_OBSERVED_HISTORICAL_IMPACT = NONE_OBSERVED**. If any R3 queries were evaluated, they were unconditionally rejected by the 0.65 ceiling (controlled abstention). There is no historical evidence that this ceiling caused a false rejection of valid R3 evidence, because R3 (lethal/severe) queries were not the primary focus of the baseline subset.

## 3. TRUST FORMULA
*Reconstructed Tier R1 calculation for a perfect candidate:*
`Trust = (0.20*1.0[auth]) + (0.20*0.0[q_rel]) + (0.15*0.0[e_qual]) + (0.10*1.0[fresh]) + (0.10*1.0[consist]) + (0.10*1.0[ent]) + (0.05*1.0[pop]) + (0.05*1.0[ap]) + (0.05*1.0[ai])`
= **0.65**

## 4. HISTORICAL TRUST RECONSTRUCTION
- **Historical anti_injection:** Gate 5 evaluated safe documents, so `poisoning_score` was exactly `0.0`. Thus, `1.0 - 0.0 = 1.0`.
- **Reconstruction Match:** The reconstructed score using the current constant `anti_injection = 1.0` and `MISSING = 0.0` perfectly matches the recorded historical scores.
- **Mismatch:** NONE for the frozen safe corpus.

## 5. OPTION A COUNTERFACTUAL
**Direct Retrieval Score Imputation:**
- *Simulation:* `query_relevance` = RRF Score / 2.
- *Delta:* Score increases by ~0.10.
- *Comparability Issue:* **Invalid.** Creates circularity (`Retrieval -> Trust -> Eligibility`). Confounds the Baseline vs Cognee experiment because graph and vector retrieval models output fundamentally different score distributions.

**Engine-Independent Relevance Imputation:**
- *Simulation:* `query_relevance` = LLM-as-a-judge or cross-encoder score.
- *Delta:* Score increases by actual relevance measurement.
- *Comparability Issue:* **Valid.** Avoids circularity. However, requires implementing a new measurement module not currently in the pipeline.

## 6. OPTION B COUNTERFACTUAL
- *Simulation:* Exclude `query_relevance` and `evidence_quality` (totaling 0.35 in R1). Scale remaining 7 factors by dividing by `0.65`.
- *Historical Score:* 0.65.
- *Option B Score:* 1.00.
- *Delta:* **+0.35** (Scores strictly shift upward; relative importance of `authority` skyrockets to >30%).
- *Result:* Invalidates all numerical scores recorded in Gate 5.

## 7. OPTION C COUNTERFACTUAL
- *Simulation:* Keep `MISSING = 0.0`.
- *Delta:* **0.0**.
- *Result:* Preserves numerical equivalence perfectly. R3 remains locked as a fail-closed safety boundary.

## 8. ANTI-INJECTION COUNTERFACTUAL
- **HISTORICAL:** `1.0 - poisoning_score` -> (for safe corpus) -> `1.0`.
- **CURRENT:** `1.0`
- **Numerical Difference:** **0.0** (Outputs are identical for the frozen experiment).
- **Methodological Difference:** Historical approach treated it as a measurement. Current approach treats it as a constant placeholder, relying strictly on the downstream hard-gate.

## 9. 3×3 COMBINATION MATRIX
| Combination | Mathematical Denominator | Historical Score Delta | Eligibility Delta (R0-R2) | Official Rerun Needed? |
|---|---|---|---|---|
| Trust A + AI A | Preserved (1.0) | +0.10 to +0.35 | Shifts (Many more pass) | YES |
| Trust B + AI A | Altered (e.g. 0.65) | +0.35 | Shifts (Threshold semantics change) | YES |
| Trust C + AI A | **Preserved (1.0)** | **0.0** | **None** | **NO** |
| Trust C + AI B | Altered (e.g. 0.95) | +0.05 | Minimal shift | YES |
*(Other combinations omitted for brevity, all result in altered denominators and require reruns).*

## 10. RERUN SCOPE
- **NO_RERUN:** Required for Trust C + Anti-Inject A. Counterfactual replay proves the outputs are numerically identical to the historical Gate 5 records.
- **FULL_GATE5_RERUN:** Required for Trust A/B or Anti-Inject B/C. Because the mathematical denominator or the measurement methodology officially changes, the historical baseline records cannot be compared against future Cognee runs. The entire 92-run offline benchmark must be regenerated.

## 11. PROTOCOL GAPS
- **Missing-Value Policy:** `SILENT`. The protocol explicitly defines the 9 factors but does not document fallback behavior.
- **Anti-Injection Semantics:** `AMBIGUOUS`. The protocol defines both a trust factor and a hard security gate, but does not clarify their continuous relationship.

## 12. THESIS CLAIM IMPLICATIONS
- **If Trust C is chosen:** Thesis can claim `"FAIL_CLOSED_WITH_MEASUREMENT_LIMITATION"`. (The system prioritizes safety by treating unmeasured factors as zeros).
- **If Trust B is chosen:** Thesis must claim `"7_FACTOR_RENORMALIZED_MODEL"`.
- **If Anti-Inject B is chosen:** Thesis can claim `"HARD_GATE_SECURITY_MODEL"`. (Injection is cleanly separated from continuous trust probability).

## 13. HUMAN DECISIONS REQUIRED
1. Trust Missing-Value Policy (A/B/C)
2. Anti-Injection Representation (A/B/C)
