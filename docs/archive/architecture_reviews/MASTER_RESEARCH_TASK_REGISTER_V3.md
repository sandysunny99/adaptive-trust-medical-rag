# MASTER RESEARCH TASK REGISTER V3

**Date:** 2026-10-03  

| Task ID | Workstream | Description | Status | Dependency | Blocker | Human Req | LLM Assist | Executable Now |
|---|---|---|---|---|---|---|---|---|
| TSK-001A| Track A | Confirm Batch 004 Annotations | ACTIVE | None | DECISION_TRACK_A_002 | YES | YES | NO (Awaiting Human) |
| TSK-001B| Track A | Complete 495 remaining annotations | PENDING | TSK-001A | None | YES | YES | NO |
| TSK-002A| Gate C | Provider Selection | BLOCKED | None | DECISION_GATE_C_001 | YES | YES | NO (Awaiting Human) |
| TSK-002B| Gate C | Provider Credential Readiness | BLOCKED | TSK-002A | Provider Credential | YES | NO | NO |
| TSK-002C| Gate C | Provider-Neutral Live Preflight | BLOCKED | TSK-002B | Live Auth | YES | NO | NO |
| TSK-003 | Claim-Evidence | Construct claim-evidence dataset schemas | READY | None | None | NO | YES | YES (Prep) |
| TSK-004 | Abstention | Build controlled abstention testing clusters | READY | None | None | NO | YES | YES (Prep) |
| TSK-005 | Security | Construct E2E malicious datasets | READY | None | None | NO | YES | YES (Prep) |
| TSK-006 | Replication | Execute valid 200-case Free Replication | PENDING | Gate C Live | None | NO | YES | NO |
| TSK-007 | Cognee | Perform Phase 1+ head-to-head evaluation | PENDING | Free Replication | None | NO | YES | NO |
| TSK-008 | Retrieval | Evaluate Recall, Precision, nDCG | PENDING | Track A Frozen | None | NO | NO | NO |
| TSK-009 | Integration | Execute final integrated validation | PENDING | TSK-006..008 | None | NO | YES | NO |
| TSK-010 | Statistics | Descriptive & Inferential Analysis | PENDING | TSK-009 | None | NO | NO | NO |
| TSK-011 | Thesis | Thesis Evidence Matrix Updates | ACTIVE | None | None | NO | NO | YES |
