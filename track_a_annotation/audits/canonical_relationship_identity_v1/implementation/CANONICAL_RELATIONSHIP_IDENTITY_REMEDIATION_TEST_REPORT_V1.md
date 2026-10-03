# Canonical Relationship Identity Remediation Test Report V1

## Test Environment
- Python 3.12
- pytest
- No external providers
- No network access
- No real LLM

## Targeted Canonical Identity Tests: 30/30 PASSED

| Test ID | Description | Status |
|---------|-------------|--------|
| RI-01 | Correct subject + correct object + correct predicate + correct direction → MATCH | ✅ PASS |
| RI-02 | Wrong predicate → MISMATCH | ✅ PASS |
| RI-03 | Wrong subject → MISMATCH | ✅ PASS |
| RI-04 | Wrong object → MISMATCH | ✅ PASS |
| RI-05 | Reverse direction → MISMATCH | ✅ PASS |
| RI-06 | Ambiguous subject → controlled failure | ✅ PASS |
| RI-07 | Unresolved object → controlled failure | ✅ PASS |
| RI-08 | RG-02 SUPPORTED but canonical mismatch → final failure | ✅ PASS |
| RI-09 | Strong NLI entailment but canonical mismatch → final failure | ✅ PASS |
| RI-10 | Canonical match + invalid citation → citation failure remains | ✅ PASS |
| RI-11 | Canonical match + low trust → trust failure remains | ✅ PASS |
| RI-12 | Full correct path → normal release | ✅ PASS |
| ADV-01 | Direction reversal adversarial attack → MISMATCH | ✅ PASS |
| PRED-01 | "inhibits" → INHIBITION | ✅ PASS |
| PRED-02 | "inhibitor" → INHIBITION | ✅ PASS |
| PRED-03 | "induces" → INDUCTION | ✅ PASS |
| PRED-04 | "increases" → INCREASES | ✅ PASS |
| PRED-05 | "contraindicated" → CONTRAINDICATION | ✅ PASS |
| PRED-06 | Unknown predicate → uppercased | ✅ PASS |
| EXT-01 | Two-drug identity extraction | ✅ PASS |
| EXT-02 | Single-drug returns None | ✅ PASS |
| EXT-03 | No predicate returns None | ✅ PASS |
| EXT-04 | Unresolved drug returns None | ✅ PASS |
| EDGE-01 | Both None → UNAVAILABLE | ✅ PASS |
| EDGE-02 | Source None → UNAVAILABLE | ✅ PASS |
| EDGE-03 | Claim None → UNAVAILABLE | ✅ PASS |
| EDGE-04 | Unknown direction → AMBIGUOUS | ✅ PASS |
| SER-01 | Identity is frozen (immutable) | ✅ PASS |
| SER-02 | EvidenceChunk backward compatible (no identity) | ✅ PASS |
| SER-03 | EvidenceChunk with identity | ✅ PASS |

## Targeted Regression Tests: 125/125 PASSED

| Test Suite | Result |
|------------|--------|
| test_claim_verifier.py | ✅ PASS |
| test_trust_scorer.py | ✅ PASS |
| test_sanitizer.py | ✅ PASS |
| test_drug_normalizer.py | ✅ PASS |
| test_mock_backend.py | ✅ PASS |
| test_security_extensions.py | ✅ PASS |

## Full Test Suite: PARTIAL_PASS_ENVIRONMENTAL_FAILURE
- test_claim_verifier_v2.py: COLLECTION ERROR (transformers not installed)
- test_claim_verifier_v2_t23.py: COLLECTION ERROR (transformers not installed)
- These are pre-existing environmental failures, not caused by this implementation.
