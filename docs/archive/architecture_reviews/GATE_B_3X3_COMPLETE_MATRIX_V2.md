# 3x3 COMPLETE DECISION MATRIX V2

**Date:** 2026-10-03  

This matrix evaluates the 9 mathematical combinations of Trust Policy (A, B, C) and Anti-Injection (A, B, C).

*Note: Trust Option A here encompasses any imputation (A1 or A2) that introduces a new non-zero variable.*

| Combination | Active Factors | Denominator | Missing Factors | Renormalization? | Mathematical Score Behavior | Historical Numerical Equivalence | Semantic Change | Methodology Change | Benchmark Impact | Official Rerun Req? |
|---|---|---|---|---|---|---|---|---|---|---|
| **Trust A + Anti A** | 9 | 1.00 | None (Imputed) | No | Scores shift up | NO (Math delta > 0) | Yes (Imputation added) | Yes (New signal) | High (A1) / Low (A2) | **YES** |
| **Trust A + Anti B** | 8 | 0.90 to 0.99 | None (Imputed) | Yes | Scores shift up/down | NO (Math delta > 0) | Yes (Hard gate) | Yes | High (A1) / Low (A2) | **YES** |
| **Trust A + Anti C** | 9 | 1.00 | None (Imputed) | No | Scores shift up/down | NO (Math delta > 0) | Yes (Probabilistic) | Yes | High (A1) / Low (A2) | **YES** |
| **Trust B + Anti A** | 7 | 0.65 to 0.70 | query, evidence | Yes | Scores shift heavily up | NO (Math delta > 0) | Yes (7-factor) | Yes | Modest (Baseline differs) | **YES** |
| **Trust B + Anti B** | 6 | 0.60 to 0.65 | query, ev, anti | Yes | Scores shift heavily up | NO (Math delta > 0) | Yes (6-factor) | Yes | Modest | **YES** |
| **Trust B + Anti C** | 7 | 0.65 to 0.70 | query, evidence | Yes | Scores shift heavily up | NO (Math delta > 0) | Yes (Probabilistic) | Yes | Modest | **YES** |
| **Trust C + Anti A** | 9 | 1.00 | query, evidence | No | Scores identical | **YES** (Delta = 0) | No (Placeholder retained) | No | None | **NO** |
| **Trust C + Anti B** | 8 | 0.90 to 0.99 | query, evidence | Yes | Scores shift slightly up | NO (Math delta > 0) | Yes (Hard gate) | Yes | Modest | **YES** |
| **Trust C + Anti C** | 9 | 1.00 | query, evidence | No | Scores shift slightly down/up | NO (Math delta > 0) | Yes (Probabilistic) | Yes | Modest | **YES** |

## Conclusion
Every combination except **Trust C + Anti A** alters the denominator or inputs, definitively breaking historical numerical equivalence and forcing a baseline rerun.
