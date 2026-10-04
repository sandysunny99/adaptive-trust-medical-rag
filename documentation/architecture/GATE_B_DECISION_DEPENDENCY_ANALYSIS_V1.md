# GATE B DECISION DEPENDENCY ANALYSIS

**Date:** 2026-10-03  
**Stage:** GATE B (Architecture Freeze)

## The Two Decisions

1. **Trust Missing-Value Policy:** How to handle unpopulated `query_relevance` and `evidence_quality` (Option A/B/C).
2. **Anti-Injection Representation:** How to handle the `anti_injection` factor, which currently operates as a constant `1.0` (Option A/B/C).

## Dependency Analysis

Are these two decisions independent? **NO.** They are mathematically coupled.

### The Coupling Mechanism

Both decisions fundamentally affect the denominator (total active weight) of the `AdaptiveTrustScorer`. 

If the researcher selects **Option B (Exclude and Renormalize)** for the Trust Missing-Value Policy, the weights for `query_relevance` and `evidence_quality` are removed. The remaining 7 weights must be scaled up so their sum equals `1.0`.

Simultaneously, if the researcher selects **Option B (Remove from continuous trust)** for the Anti-Injection Representation, the weight for `anti_injection` is also removed.

### Scenario Interactions

- **Scenario 1:** Option C for Trust (Keep 0.0) + Option A for Anti-Injection (Keep 1.0).
  - *Result:* No mathematical change. Gate 5 is perfectly preserved. The denominator remains 1.0. R3 remains locked.
  
- **Scenario 2:** Option B for Trust (Exclude) + Option B for Anti-Injection (Exclude).
  - *Result:* Three factors are removed. For Risk Tier R1, the total removed weight is `0.20 + 0.15 + 0.05 = 0.40`. 
  - The remaining 6 weights must be divided by `0.60`. 
  - This radically alters the comparative importance of `source_authority` and `freshness`.
  - Gate 5 must absolutely be rerun.

- **Scenario 3:** Option A for Trust (Impute) + Option B for Anti-Injection (Exclude).
  - *Result:* Circularity is introduced via Option A. The `anti_injection` weight is removed. The denominator drops slightly (e.g., by 0.05). Gate 5 must be rerun.

## Conclusion

Because both decisions define the mathematical boundaries of the trust formula, they must be decided concurrently. Changing one alters the normalization denominator of the other if any exclusion policy is chosen. 

They are **coupled methodological decisions** that will dictate whether Gate 5 must be regenerated.
