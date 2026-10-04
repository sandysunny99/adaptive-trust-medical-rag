# CLAIM-EVIDENCE ABSTENTION AUDIT

Can the following independently trigger ABSTAIN?
- **Unsupported critical claim**: YES (`ClaimVerifierV2.verify`).
- **Insufficient evidence (critical)**: YES (`ClaimVerifierV2.verify`).
- **Missing trust factors**: YES (Pre-generation in orchestrator, but NOT post-generation).
- **Contradiction**: YES (`ClaimVerifierV2` detects and returns abstain).
- **Unsupported relationship**: YES (Pre-generation via `RG-02`, but NOT post-generation).
