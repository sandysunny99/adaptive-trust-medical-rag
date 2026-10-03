# TRUST P0 MISSING DATA TEST MATRIX V2

1. **all trust factors present**: Score 1.0 (pass).
2. **one non-critical factor missing**: Score 0.9 (pass R0-R3).
3. **one safety-critical missing**: Score 0.8 (pass R0-R3).
4. **multiple factors missing**: Score drops drastically.
5. **all required factors missing**: Score 0.0 (fails all).
6. **explicit zero**: Functions identical to missing for aggregate score (0 contribution) but distinguishable by `missing_factors` list.
7. **explicit one**: Increases score (unlike missing).
8. **R3 + complete evidence**: Passes R3 gate.
9. **R3 + missing required evidence**: Fails R3 gate due to score dilution.
