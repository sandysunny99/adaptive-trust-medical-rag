# TRUST P0 FULL REGRESSION V2

- **pytest tests/test_trust_scorer.py**: 38/38 tests PASS.
- **pytest tests**: Fails on 2 `claim_verifier` test files due to an environmental `ModuleNotFoundError: transformers`.
- **Conclusion**: PARTIAL_PASS_ENVIRONMENTAL_FAILURE. No regression in trust logic.
