# TEST COVERAGE AUDIT

- `test_claim_verifier_v2.py`: Covers Atomic decomposition, basic NLI thresholding, ambiguity detection, contradiction detection. (UNIT_VALIDATED).
- `test_provider_runtime_integration.py`: Tests the orchestrator pipeline. (INTEGRATION_VALIDATED).
- **Gaps**: No tests explicitly enforce that `citation_supports_claim == False` must trigger an `abstain` or claim removal. No tests simulate `missing_factors` reaching the claim verifier.
