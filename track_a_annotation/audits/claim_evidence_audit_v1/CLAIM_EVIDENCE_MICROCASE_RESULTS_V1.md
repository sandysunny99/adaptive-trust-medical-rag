# CONTROLLED OFFLINE MICRO-CASES

*(Tested via local mock simulation of ClaimVerifierV2)*

- **CASE A (Direct Support)**: `SUPPORTED` -> `GateDecision.release`.
- **CASE B (Partial Support)**: Mapped to `SUPPORTED` (if ent dominates con/neu) -> `GateDecision.release`.
- **CASE C (Unsupported)**: `INSUFFICIENT_EVIDENCE` -> `GateDecision.qualify` (or `abstain` if critical).
- **CASE D (Contradictory)**: `CONTRADICTED` -> `GateDecision.abstain`.
- **CASE E (Missing Provenance)**: Claim cites Source 2, evidence is in Source 1. Claim is marked `SUPPORTED`. Citation validates to False, but Gate Decision is `release`. -> **PROVENANCE GAP VERIFIED**.
- **CASE I (Mixed Evidence)**: `AMBIGUOUS` -> `GateDecision.abstain`.
