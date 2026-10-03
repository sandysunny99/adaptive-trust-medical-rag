# RELATIONSHIP REGRESSION REPORT
- **Goal**: Enforce RG-02 block semantics at the claim level.
- **Test**: `scratch/test_remediation.py` -> `run_case("P1 RELATIONSHIP REGRESSION", ...)`
- **Result**: Claim is marked `UNSUPPORTED` if `relationship_scope` is `NO_RELEVANT_RELATION`.
