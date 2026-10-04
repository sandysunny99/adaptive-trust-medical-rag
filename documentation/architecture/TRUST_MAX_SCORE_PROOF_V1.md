# TRUST MAX SCORE PROOF

**Date:** 2026-10-03  

This proof calculates the absolute maximum possible trust score for each risk tier, assuming every populated variable achieves a perfect `1.0` score, while `query_relevance` and `evidence_quality` remain their current default of `0.0`.

## Calculations

**Risk Tier R0:**
- Configured Total: `1.00`
- Missing Weights: `query_relevance (0.20) + evidence_quality (0.10) = 0.30`
- **Maximum Achievable Score:** `1.00 - 0.30 = 0.70`
- **Threshold:** `0.30`
- **Conclusion:** Reachable.

**Risk Tier R1:**
- Configured Total: `1.00`
- Missing Weights: `query_relevance (0.20) + evidence_quality (0.15) = 0.35`
- **Maximum Achievable Score:** `1.00 - 0.35 = 0.65`
- **Threshold:** `0.45`
- **Conclusion:** Reachable.

**Risk Tier R2:**
- Configured Total: `1.00`
- Missing Weights: `query_relevance (0.15) + evidence_quality (0.20) = 0.35`
- **Maximum Achievable Score:** `1.00 - 0.35 = 0.65`
- **Threshold:** `0.60`
- **Conclusion:** Reachable.

**Risk Tier R3:**
- Configured Total: `1.00`
- Missing Weights: `query_relevance (0.10) + evidence_quality (0.25) = 0.35`
- **Maximum Achievable Score:** `1.00 - 0.35 = 0.65`
- **Threshold:** `0.75`
- **Conclusion:** IMPASSABLE.

**Note on `anti_injection`:** The constant `1.0` value for `anti_injection` is mathematically **included** in these maximum calculations. It provides a constant `+0.01` to `+0.10` bonus depending on the tier. Without it, the max scores would be even lower.
