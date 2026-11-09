# OPTION B: RENORMALIZATION ANALYSIS

**Date:** 2026-10-03  
**Proposal:** Exclude `query_relevance` and `evidence_quality` from the formula and mathematically scale the remaining 7 weights so they sum to 1.0.

## 1. Exact Renormalized Weights (Tier R1 Example)

- **Original Denominator:** `1.0`
- **Removed Weight:** `query_relevance (0.20) + evidence_quality (0.15) = 0.35`
- **New Denominator:** `0.65`

| Factor | Original Weight | New Weight (Weight / 0.65) | Relative Change |
|---|---|---|---|
| `authority` | 0.20 | 0.307 | Increased |
| `freshness` | 0.10 | 0.153 | Increased |
| `consistency` | 0.10 | 0.153 | Increased |
| `entity_match` | 0.10 | 0.153 | Increased |
| `population_match` | 0.05 | 0.076 | Increased |
| `anti_poisoning` | 0.05 | 0.076 | Increased |
| `anti_injection` | 0.05 | 0.076 | Increased |

## 2. Consequences

- **Threshold Semantics:** Because `authority` now controls over 30% of the total score, the "price" of retrieving from a lower-tier medical journal skyrockets. A candidate with low authority is far more likely to fail the threshold.
- **Historical Comparability:** Every single trust score generated during the Gate 5 frozen benchmark is mathematically incomparable to future scores.
- **Methodology Impact:** Fundamentally alters the architecture from a 9-factor model into a 7-factor model.
- **Rerun Requirement:** The entire 92-run Gate 5 baseline MUST be re-executed from scratch to establish a valid comparative baseline for Cognee.
