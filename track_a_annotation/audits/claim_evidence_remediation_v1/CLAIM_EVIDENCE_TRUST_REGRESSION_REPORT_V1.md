# TRUST REGRESSION REPORT
- **Goal**: Propagate `missing_factors` to the verifier.
- **Test**: `scratch/test_remediation.py` -> `run_case("P1 TRUST REGRESSION", ...)`
- **Result**: Metadata safely reaches `SemanticJudgment` without being dropped.
