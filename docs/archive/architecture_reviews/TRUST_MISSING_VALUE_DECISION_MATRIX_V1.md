# TRUST MISSING-VALUE DECISION MATRIX

**Date:** 2026-10-03  
**Stage:** GATE B (Architecture Freeze)  
**Status:** 🔒 HUMAN_DECISION_REQUIRED = YES

## The Core Issue

In `trust_scorer.py`, `query_relevance` and `evidence_quality` default to `0.0`. In the orchestrator, they are never populated. 
- **Configured Weights (R1):** `query_relevance` (0.20), `evidence_quality` (0.15).
- **Mathematical Impact:** Maximum achievable trust score is locked at `0.65`.
- **Threshold Impact:** Risk Tier R3 (threshold 0.75) is mathematically impassable.

## Decision Matrix

| Criterion | Option A: Impute from Existing Signals | Option B: Exclude and Renormalize | Option C: Keep MISSING = ZERO |
|-----------|----------------------------------------|-----------------------------------|-------------------------------|
| **Description** | Derive `query_relevance` from RRF or cosine similarity. Derive `quality` from metadata defaults. | Remove the 2 missing factors from the formula. Scale up the remaining 7 weights proportionally. | Accept the 0.0 defaults. Acknowledge R3 is unreachable. |
| **Scientific Interpretability** | High, assuming the mapping is monotonic and bounded (e.g., cosine similarity `[0,1]`). | High. The formula remains mathematically coherent based on available signals. | Low. The formula penalizes chunks not because they are bad, but because the pipeline lacks measurement capability. |
| **Threshold Validity** | Restores reachability for all thresholds (R0-R3). | Restores reachability for all thresholds (R0-R3). | Invalidates R3 entirely. |
| **Retrieval Independence** | **CRITICAL RISK:** Deriving trust from retrieval score (e.g., RRF) creates circularity. It makes the independent Trust Layer partially dependent on the specific retrieval engine. | Safe. Independent of retrieval scores. | Safe. Independent of retrieval scores. |
| **Baseline vs Cognee Comparability** | **POOR.** If Cognee produces differently scaled similarity scores than BM25/Vector, the Trust score shifts mechanically, confounding the experiment. | Excellent. Removes the confounding variables entirely. | Excellent. Constant penalty affects both engines equally. |
| **Methodological Change** | **Major.** Fundamentally alters the definition of trust to include retrieval confidence. | **Moderate.** Changes the 9-factor architectural blueprint into a 7-factor model. | **None.** Preserves the exact state as originally executed. |
| **Implementation Complexity** | High. Requires score normalization across diverse retrieval engines (BM25 is unbounded, Vector is cosine). | Medium. Requires updating `trust.yaml` weights. | Zero. |
| **Historical Reproducibility** | Breaks Gate 5. Prior results must be regenerated. | Breaks Gate 5. Prior results must be regenerated. | Preserves Gate 5 exactly. |

## Conclusion

**HUMAN_DECISION_REQUIRED = YES**

Option A introduces severe methodological risks (circularity and loss of cross-engine comparability). Option B requires formally amending the 9-factor trust architecture. Option C preserves historical reproducibility but sacrifices the R3 risk tier.

The research owner must explicitly authorize one of these paths before Gate B can be closed.
