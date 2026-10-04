# GATE B FINAL DECISION BRIEF

**Date:** 2026-10-03  
**Stage:** GATE_B  

## Decision Question
1. **TRUST MISSING-VALUE POLICY:** How should unavailable trust measurements (`query_relevance`, `evidence_quality`) be represented?
2. **ANTI-INJECTION REPRESENTATION:** Should prompt injection remain in continuous trust as a placeholder, or be treated solely as a hard security property?

## Current Evidence
- **Mathematical Bound:** Max achievable trust score is 0.65 for R1-R3. R3 (0.75 threshold) is mathematically impassable.
- **Historical Numerical Equivalence:** Historical Gate 5 used a clean safe corpus (`poisoning=0.0`), meaning the old `anti_injection` math (`1.0 - 0.0`) yielded `1.0`. The current patch (`1.0`) is numerically identical for that corpus.
- **Protocol Silence:** The normative architecture protocol does NOT explicitly define `MISSING=0.0` as a fail-closed safety rule; it is an observed implementation behavior.

## Unverified
- **R3 Historical Impact:** It is unverified whether the Gate 5 evaluation actually processed any R3 (Lethal/Severe) queries. If no R3 queries were present, the 0.65 trust ceiling caused zero actual rejections in the historical baseline.

## 3x3 Matrix
| Combination | Semantic Interpretation | Mathematical Effect | Historical Compatibility | Rerun Required? |
|---|---|---|---|---|
| **Trust A (1/2) + Anti A** | Imputation + Placeholder | Scores shift up | BROKEN | **YES** |
| **Trust A (1/2) + Anti B** | Imputation + Hard Gate | Scores shift up, Denom alters | BROKEN | **YES** |
| **Trust A (1/2) + Anti C** | Imputation + Continuous | Scores shift up, Signal alters | BROKEN | **YES** |
| **Trust B + Anti A** | 7-factor + Placeholder | Denominator shrinks (e.g. 0.65) | BROKEN | **YES** |
| **Trust B + Anti B** | 6-factor + Hard Gate | Denom shrinks severely | BROKEN | **YES** |
| **Trust B + Anti C** | 7-factor + Continuous | Denom shrinks | BROKEN | **YES** |
| **Trust C + Anti A** | Missing=0 + Placeholder | **Preserves exact 1.0 Denom** | **PRESERVED (Numerical Eq.)** | **NO** |
| **Trust C + Anti B** | Missing=0 + Hard Gate | Denominator shrinks (e.g. 0.95) | BROKEN | **YES** |
| **Trust C + Anti C** | Missing=0 + Continuous | Signal alters | BROKEN | **YES** |

## Option A1 (Direct Retrieval Imputation)
Imputes relevance from retrieval scores (e.g., BM25/Cosine). Invalidates independent Baseline vs Cognee comparability due to circularity. Changes missing-value behavior. Incompatible with historical artifacts. Requires mandatory rerun.

## Option A2 (Independent Relevance Measurement)
Imputes relevance using a new post-retrieval module (cross-encoder/LLM-judge). Scientifically valid, avoids circularity. Still requires mandatory rerun. High implementation burden.

## Option B (Renormalization)
Excludes missing dimensions entirely. Reduces pipeline to a 7-factor model. Heavily alters score behavior (scales remaining weights). Requires mandatory rerun. Preserves nothing of Gate 5 numerical outputs.

## Option C (Keep Missing=0.0)
Preserves the observed implementation behavior. Produces conservative score depression (30-35%). Preserves historical numerical outputs perfectly (Delta=0). Not yet a proven "normative design" without human authorization, but serves as a pragmatic measurement limitation.

## Gate 5 Rerun Dependency
- **NOT REQUIRED:** Trust Option C + Anti-Injection Option A. (Maintains numerical equivalence).
- **MANDATORY RERUN:** All other combinations. Any shift in mathematical denominator or score behavior invalidates the historical baseline records for comparison against Cognee.

## Historical Result Treatment
Historical results must be treated as **HISTORICAL** engineering observations, mathematically preserved ONLY if C+A is selected. No historical ledgers, manifests, or scores may be overwritten.

## Scientific Claim Impact
- "R3 is locked out due to measurement deficiency" -> **SUPPORTED NOW** (Historical Observation).
- "Missing=0 is an intentional fail-closed safety design" -> **NOT SUPPORTED** (Requires protocol change authorization).
- "Trust layer mitigates hallucinations effectively" -> **SUPPORTED ONLY AFTER RERUN / END-TO-END VALIDATION**.

---
## DECISION-SUPPORT CONCLUSION

**MOST EVIDENCE-PRESERVING OPTION:** Trust Option C + Anti-Injection Option A.
**WHY:** This is the *only* combination that guarantees historical numerical equivalence (Delta=0.0) with the frozen Gate 5 records. The historical `1.0 - poisoning` expression mathematically evaluated to `1.0` for the safe corpus, matching the current patch. 
**RERUN REQUIRED:** CONDITIONAL (No if C+A; Yes otherwise).
**RERUN SCOPE:** NOT REQUIRED (if C+A).
**HISTORICAL ARTIFACTS PRESERVED:** YES (if C+A).
**CODE CHANGE REQUIRED:** NO (if C+A).

**SCIENTIFIC CLAIMS ENABLED:** 
- "Pipeline implements a conservative measurement limitation for missing factors."
- "Anti-injection operates functionally as a hard security gate, utilizing continuous trust structurally but not probabilistically."

**SCIENTIFIC CLAIMS STILL BLOCKED:** 
- "The trust layer intentionally fails-closed based on normative protocol design." (Unless formally adopted).
- Generative E2E security claims (Blocked pending real LLM credential).
