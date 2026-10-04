# RESEARCH EXECUTION DEPENDENCY MAP

**Date:** 2026-10-03  
**Project Stage:** CONTROLLED SCIENTIFIC VALIDATION

| Workstream | Status | Dependencies | Can Execute Now | Human Decision Req | Live Provider Req | Frozen Touch Req | Output Artifacts |
|---|---|---|---|---|---|---|---|
| **Track A Annotation** | ACTIVE | None | YES | YES | NO | NO | `TRACK_A_WORKSPACE_V1.jsonl` |
| **Gate C Preflight** | BLOCKED | `GEMINI_API_KEY` | NO | YES (Inject key) | YES | NO | `GATE_C_READINESS_V1` |
| **Gate C Live Execution**| PENDING | Gate C Preflight | NO | NO | YES | NO | `GATE_C_REPORT_V1` |
| **Claim-Evidence Eval**| READY | Track A (partial) | YES (Prep) | NO | NO | NO | `CLAIM_EVIDENCE_BENCHMARK_V1` |
| **E2E Security Eval** | PENDING | Gate C | NO | NO | YES | NO | `E2E_SECURITY_REPORT_V1` |
| **Controlled Abstention**| READY | None | YES (Prep) | NO | NO | NO | `ABSTENTION_DATASET_V1` |
| **Free Replication** | PENDING | Gate C | NO | NO | YES | NO | `REPLICATION_200_REPORT_V1` |
| **Cognee Scientific Eval**| PENDING | Free Replication | NO | NO | YES | NO | `COGNEE_EVALUATION_V1` |
| **Final Integrated Eval**| PENDING | All above | NO | NO | YES | NO | `INTEGRATED_VALIDATION_V1` |
| **Statistical Analysis** | PENDING | Integrated Eval | NO | NO | NO | NO | `STATISTICS_REPORT_V1` |
| **Thesis Evidence Matrix**| ACTIVE | All above | YES | NO | NO | NO | `THESIS_EVIDENCE_MATRIX_V1.md` |
