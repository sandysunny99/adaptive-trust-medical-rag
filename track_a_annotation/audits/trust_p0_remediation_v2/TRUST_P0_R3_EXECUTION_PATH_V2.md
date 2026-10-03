# TRUST P0 R3 EXECUTION PATH V2

1. **QUERY**: Classified as R3 (High-Risk).
2. **EVIDENCE**: Chunks fetched.
3. **TRUST FACTORS**: Extracted per chunk. Missing factors set to `None`.
4. **R3**: Threshold 0.75. Scorer computes `numerator (available evidence) / 1.0 (full denominator)`. 
5. **ABSTENTION / BLOCK**: If sparse evidence yields a score < 0.75, `is_eligible = False`.
6. **CLAIM OUTPUT**: Blocked for this chunk.
