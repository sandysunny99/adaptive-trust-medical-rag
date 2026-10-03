# TRUST P0 BEFORE/AFTER BEHAVIOR V1

**BEFORE IMPLEMENTATION:**
Missing `query_relevance` defaulted to `0.0`, dragging trust scores to the floor silently. Missing `population_match` defaulted to `1.0`, artificially inflating trust scores.

**AFTER REMEDIATION:**
Missing factors are explicitly stored as `None`. `AdaptiveTrustScorer` excludes them, recalculating the score proportionately to the available evidence pool.

**OBSERVED DIFFERENCE:**
Explicit explicit 0/1 calculations are demonstrably different from missing data calculations.
