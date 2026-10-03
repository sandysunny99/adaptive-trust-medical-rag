# TRUST P0 REMEDIATION V2 TARGET POLICY

- **A. Missing factor behavior**: Explicitly recorded as `None` in `missing_factors`. Contributes `0.0` to the scoring numerator, but its weight REMAINS in the scoring denominator.
- **B. Incomplete evidence behavior**: Because missing factors dilute the numerator without shrinking the denominator, incomplete evidence mathematically produces a lower trust score.
- **C. R3/high-risk cases**: With a strict threshold (0.75), R3 mathematically requires high completeness. Missing required evidence drags the score below 0.75, enforcing the mandated abstention.
- **D. Normal numeric trust score**: A valid numeric score is produced, but its magnitude is proportionally diluted by missing data, accurately reflecting the lack of overall confidence.
- **E. Final claim eligibility**: Sparse evidence fails the hard threshold gates.
- **F. Controlled abstention**: Triggered naturally when the diluted trust score falls below the required risk-tier threshold.
- **G. Mandatory vs optional factors**: Handled mathematically. Heavy-weight factors cause larger score drops if missing.
- **H. Missingness effect**: Both exposes the `missing_factors` list (gate status) AND affects the trust score magnitude.
