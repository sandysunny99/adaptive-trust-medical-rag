# CLAIM-EVIDENCE THRESHOLD AUDIT

| Threshold | Value | Component | Purpose | Validation |
|---|---|---|---|---|
| Contradiction Activation | `max_con > 0.4` | `_map_to_state` | Prevent low-confidence noise from triggering contradiction | UNIT_VALIDATED |
| Contradiction Margin | `max_con - max_ent >= 0.3` | `_map_to_state` | Ensure contradiction strongly dominates entailment | UNIT_VALIDATED |
| Ambiguity Margin | `abs(max_ent - max_con) < 0.1` | `_map_to_state` | Detect conflicting NLI signals | UNIT_VALIDATED |
| Insufficient Evidence | `max_neu > 0.7` | `_map_to_state` | Treat high neutral scores as unsupported | UNIT_VALIDATED |
