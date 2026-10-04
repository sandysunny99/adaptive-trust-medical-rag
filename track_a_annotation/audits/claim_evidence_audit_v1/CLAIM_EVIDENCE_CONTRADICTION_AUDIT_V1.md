# CLAIM-EVIDENCE CONTRADICTION AUDIT

- **Direct Contradiction**: Detected via NLI `contradiction` score dominating `entailment`. Maps to `FinalSupportState.CONTRADICTED`.
- **Tension/Mixed Evidence**: If one chunk entails and another contradicts strongly, `ClaimVerifierV2` marks it `FinalSupportState.AMBIGUOUS`.
- **Action**: Any claim marked `CONTRADICTED` or `AMBIGUOUS` forces `GateDecision.abstain`.
- **Result**: Mixed/contradictory evidence successfully halts the pipeline and triggers controlled abstention.
