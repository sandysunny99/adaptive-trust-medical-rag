# TRUST P0 BEFORE / V1 / V2 COMPARISON

- **A. ORIGINAL (Hidden defaults):** `query_relevance` missing -> `0.0`. `population_match` missing -> `1.0`. Silently inflated/deflated confidence.
- **B. REMEDIATION V1 (Available-factor exclusion):** Missing factors explicitly `None`, but excluded from denominator. Inflated confidence of sparse evidence.
- **C. REMEDIATION V2 (Safety-consistent full denominator):** Missing factors explicitly `None`. Full denominator retained. Sparse evidence accurately dilutes confidence, enforcing specified abstention rules.
