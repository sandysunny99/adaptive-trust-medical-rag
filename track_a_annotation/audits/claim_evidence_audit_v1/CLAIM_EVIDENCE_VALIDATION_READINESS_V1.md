# VALIDATION READINESS

- **Status**: FINDINGS_REQUIRE_ENGINEERING
- The structural gap in `ClaimVerifierV2`'s handling of provenance (ignoring `citation_supports_claim`) must be engineered before Controlled Abstention can be scientifically validated. If we validate now, the system will incorrectly pass hallucinated citations.
