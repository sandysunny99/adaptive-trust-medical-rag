# TRUST P0 IMPLEMENTATION CHANGE REPORT V2

Removed undocumented available-factor exclusion from `trust_scorer.py`:
- `weight_sum = sum(weights[f] for f in TRUST_FACTORS)` (Full sum equals 1.0 per config).
- Missing factors (`None`) appended to `missing_factors` list and bypassed in numerator computation.
- Output: Properly diluted trust score that accurately reflects overall evidentiary confidence.
