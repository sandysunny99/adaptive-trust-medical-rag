# MIXED CLAIM ANALYSIS
- `AnswerSafetyGate` computes `grounding_ratio`.
- E.g., 3 Supported, 1 Unsupported -> 75% Grounded.
- If `confidence_threshold` is 0.80, a 75% grounded answer triggers `GateDecision.abstain`.
