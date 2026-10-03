# P0 REGRESSION REPORT
- **Goal**: Prevent claim from being supported by unrelated chunk.
- **Test**: `scratch/test_remediation.py` -> `run_case("P0 REGRESSION", ...)`
- **Result**: Claim is marked `UNSUPPORTED`, preventing leakage.
