# PROVENANCE REMEDIATION DESIGN
Target: Ensure a claim is only supported if its EXPLICITLY cited evidence supports it.
Design:
- Extracted `citation_supports` logic from `ClaimVerifierV2.verify`.
- Added a block enforcing that `state = FinalSupportState.UNSUPPORTED` if `citation_supports` is False, overriding the global entailment state.
- Uncited claims are mapped to `UNSUPPORTED`.
