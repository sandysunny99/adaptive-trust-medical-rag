# 3x3 DECISION DEPENDENCY MATRIX

**Date:** 2026-10-03  

## Decisions
1. **Trust Policy:** A (Impute), B (Renormalize), C (Keep 0.0)
2. **Anti-Inject:** A (Keep 1.0), B (Remove/Renormalize), C (New continuous signal)

## Matrix Analysis

| Combination | Mathematical Denominator | Security Semantics | Gate 5 Rerun Required? |
|---|---|---|---|
| **Trust A + Anti A** | Preserved (1.0) | Placeholder (1.0 bonus) | **YES** (Trust circularity changes scores) |
| **Trust A + Anti B** | Altered | Formally hard-gate | **YES** (Score circularity + denom change) |
| **Trust A + Anti C** | Preserved (1.0) | Continuous probability | **YES** (Trust circularity + new signal) |
| **Trust B + Anti A** | Altered (e.g. 0.65) | Placeholder (bonus scaled up) | **YES** (Trust denom changes) |
| **Trust B + Anti B** | Altered (e.g. 0.60) | Formally hard-gate | **YES** (Double denom change) |
| **Trust B + Anti C** | Altered (e.g. 0.65) | Continuous probability | **YES** (Trust denom changes) |
| **Trust C + Anti A** | **Preserved (1.0)** | **Placeholder (1.0 bonus)** | **NO** (Exact match to historical math) |
| **Trust C + Anti B** | Altered (e.g. 0.95) | Formally hard-gate | **YES** (Anti-Inject denom changes) |
| **Trust C + Anti C** | Preserved (1.0) | Continuous probability | **YES** (New signal math) |

## Conclusion
Only ONE combination (**Trust Option C + Anti-Injection Option A**) mathematically preserves the exact continuous trust formula used in the frozen Gate 5 experiments, allowing progress to Gate C without a massive baseline rerun.
