# Runtime Provenance Audit V4

## Source of Artifacts
- All artifacts generated in V3 and V4 audits were derived directly from the execution of `experiments/gate5_readiness_v3.py`.
- No hardcoded `RELEASE` or `BLOCK` results were detected in the execution harness for specific cases.
- The V3 trace includes `"evidence_source": "runtime_capture"`.

## Target Filtering
- No `target_doc`, `expected_doc_id`, or `lambda` filters were used to massage candidates. The retrieval operated natively on the corpus.

## Missing Artifacts
- `COGNEE_LIVE_SECURITY_TRACE_V4.jsonl` is empty because `gate5_readiness_v3.py` explicitly excluded Cognee from the full orchestrator path, relying instead on the separate `cognee_readiness_v3.py` probe. As a result, no real Cognee runtime trace through the security pipeline was captured.

## Conclusion
The captured data is authentic to the system's execution, which legitimately demonstrates the flaws that prevent final readiness from being declared.
