# REASON TRACEABILITY
- Pre-Gen Abstention: Returns reason string directly from `EligibilityGate`.
- Post-Gen Abstention: `VerificationReportV2` stores detailed `SemanticJudgment`s for every claim, including `missing_factors` and `relationship_scope`.
- `_abstain` captures this via the `verification` kwarg.
