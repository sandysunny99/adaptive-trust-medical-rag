# INVALID_RUN

**Run ID:** phase13a_exec_1
**Execution Timestamp:** 2026-09-05T13:04:22Z (from run_manifest.json)
**Case Count:** 7 (5 attack cases)

## Classification
**FORENSIC / EXPLORATORY / INVALID SCIENTIFIC RUN**

## Reasons for Invalidation
1. **Premature Execution:** Executed without explicit user approval after the infrastructure gate.
2. **Insufficient Sample Size:** Only 7 synthetic cases (5 attacks); insufficient for the planned scientific evaluation.
3. **Simulation Artifacts:** BASELINE is a security-boundary simulation adapter, not the actual historical RAG pipeline.
4. **Unsupported Inference:** Statistical comparison (McNemar statistic) is not suitable as a substantive inference with this tiny case count/design.
5. **Fixture-Derived Metrics:** PPR is fixture-derived rather than measuring provenance preservation through a realistic processing path.

## Scientific Inference Policy
* **No scientific conclusions may use this run.**
* The ADR, ABR, FPR, UAR, PPR, and McNemar statistic values are **EXPLORATORY / INVALID FOR SCIENTIFIC INFERENCE**.
* Do not use the numerical values or narrative conclusions from this run in the thesis, paper, abstract, presentation, or final evaluation.

*The raw artifacts (`results.jsonl`, `run_manifest.json`, `report.md`) are retained in this directory strictly for auditability.*
