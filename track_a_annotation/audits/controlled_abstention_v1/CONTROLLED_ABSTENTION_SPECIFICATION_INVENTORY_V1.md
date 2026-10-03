# SPECIFICATION INVENTORY

| Rule | Source File | Section | Exact Semantics | Implementation Counterpart | Validation Evidence |
|---|---|---|---|---|---|
| R0-R3 Thresholding | `trust.yaml` | Thresholds | R0=0.30, R1=0.45, R2=0.60, R3=0.75 | `EvidenceEligibilityGate` | Unit tested |
| Missing Evidence Abstention | `AGENTS.md` | Section 2.4 | System must abstain when evidence is missing | `EvidenceEligibilityGate.MIN_ELIGIBLE_CHUNKS` | Execution Trace |
| Citation Support | `AGENTS.md` | Section 2.1 | Never generate claims without explicit retrieved evidence | `ClaimVerifierV2.verify` | Adversarial Microcases |
| Contradiction Abstention | `AGENTS.md` | Section 2.4 | System must abstain when evidence is unresolvably contradictory | `ClaimVerifierV2` / `GateDecision.abstain` | Unit tested |
