# R3 ABSTENTION AUDIT
- **Threshold**: 0.75
- **Weights**: Highly biased toward `source_authority` (0.30) and `evidence_quality` (0.25).
- **Missing Required Data**: If `source_authority` or `evidence_quality` is missing, the theoretical maximum score drops to 0.70 or 0.75. Due to realistic minor penalties, it practically guarantees failing the 0.75 threshold.
- **Behavior**: Chunks failing R3 are dropped. If no chunks remain, `_abstain()` is called pre-generation.
