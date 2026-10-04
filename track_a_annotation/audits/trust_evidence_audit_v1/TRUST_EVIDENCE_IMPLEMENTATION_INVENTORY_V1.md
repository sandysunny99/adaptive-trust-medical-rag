# TRUST EVIDENCE IMPLEMENTATION INVENTORY V1
| Component | File | Function/Class | Input | Output | Current Test Coverage | Validation Level |
|---|---|---|---|---|---|---|
| Trust Scorer | `src/.../trust_scoring/trust_scorer.py` | `AdaptiveTrustScorer` | `TrustFactorScores` | `TrustScoringResult` | Unit | UNIT_VALIDATED |
| Claim Verifier | `src/.../verification/claim_verifier_v2.py` | `ClaimVerifierV2` | Claims | `VerificationReportV2` | Unit | UNIT_VALIDATED |
| Rel. Grounding | `src/.../security_extensions/relationship_grounding_v2.py` | `RelationshipGroundingValidatorV2` | Context | `GroundingDecision` | Security Integration | ADAPTER_LEVEL_VALIDATED |
| Source Validator | `src/.../source_validation/source_validator.py` | `SourceValidator` | Source ID | Auth Score | Unit | UNIT_VALIDATED |
