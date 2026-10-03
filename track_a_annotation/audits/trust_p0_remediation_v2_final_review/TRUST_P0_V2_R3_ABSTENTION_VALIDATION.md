# TRUST P0 V2 R3 ABSTENTION VALIDATION

- R3 threshold is 0.75. 
- With full denominator retained, omitting heavily weighted factors (like `evidence_quality` = 0.25) drops the maximum possible score to 0.75, making it mathematically impossible to pass unless all other factors are perfect.
- Thus, R3 mathematically requires high completeness (required missing evidence triggers abstention).
- This aligns precisely with `AGENTS.md` and `medical-safety.md`.
