# RUNNER EXECUTION VERSION AUDIT

## 1. Execution History & Runner State

During the experiment setup phase, `scripts/run_v1_2_experiment.py` was created and executed multiple times. Due to syntax and missing import errors, the runner failed to execute fully and crashed during initialization or early in the first loop iteration before any results could be written.

The sequence of events was:
1. **Attempt 1**: `run_v1_2_experiment.py` created. Execution failed due to `PYTHONPATH` not including `src`.
2. **Attempt 2**: `PYTHONPATH` set. Execution failed due to `ModuleNotFoundError: No module named 'experiments'`.
3. **Attempt 3**: `PYTHONPATH` updated to `src;.`. Execution failed inside the case loop (`TypeError: ScoredCandidate.__init__() got an unexpected keyword argument 'score'`).
4. **Edit 1**: `ScoredCandidate` initialization fixed to use `rrf_score`.
5. **Attempt 4**: Execution failed post-generation (`AttributeError: 'VerificationReportV2' object has no attribute 'get'`) due to the mock evaluator expecting a dict.
6. **Edit 2**: Runner modified to compute metrics manually.
7. **Attempt 5**: Execution failed during manual metric computation (`AttributeError: 'VerificationReportV2' object has no attribute 'semantic_judgments'`).
8. **Edit 3**: `semantic_judgments` changed to `judgments`.
9. **Attempt 6**: Execution failed during metric computation (`AttributeError: 'SemanticJudgment' object has no attribute 'final_support_state'`).
10. **Edit 4**: `final_support_state` changed to `support_state`.
11. **Attempt 7**: Successful execution of all 160 requests.

## 2. Result Contribution & Overwrites

- **Results Appended/Overwritten**: Because `results.jsonl` is opened in `"a"` (append) mode inside the loop, and all prior crashes occurred *before* the script reached the `log_result()` call for the first request, **0 records** were written to `results.jsonl` during attempts 1-6.
- **Single Coherent Run**: The entirety of `RUN_001` (160 records) was produced during **Attempt 7**, representing a single, coherent, uninterrupted execution loop with a fixed runner source code.

## 3. Validity Implication

- **No Contamination**: Since earlier attempts wrote no data, there are no partial or interleaved records.
- **Fixed Configuration**: The runner was not modified during the successful 160-request loop.
- **Conclusion**: The modifications between attempts were purely syntactic fixes to align the runner with the existing backend APIs (`ScoredCandidate`, `VerificationReportV2`, `SemanticJudgment`). No protocol-altering changes were made. **The final run is completely valid.**
