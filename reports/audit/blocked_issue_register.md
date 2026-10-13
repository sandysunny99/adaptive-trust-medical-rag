# Blocked Issue Register

**Current revision:** `d7b068779bcb2d64e062ef444c280281e54f4cd3`

| ID | Severity | Type | Evidence | Required action | Owner | Dependencies | Acceptance criteria | Status |
|---|---|---|---|---|---|---|---|---|
| B-LIVE-EXTRACTION | Critical | Provider configuration | No supported live LLM/vision credentials configured; deterministic image tests pass | Configure authorized server-side credentials without committing secrets | Researcher/admin | quota, model access | Controlled synthetic image request completes or reports exact provider failure | BLOCKED_EXTERNAL_DEPENDENCY |
| B-HUMAN-RELEVANCE | Critical | Missing ground truth | Track A has frozen 530-position inputs but incomplete human labels; strict V3.1 audit rejects heuristic labels | Complete blinded researcher annotation/adjudication | Researcher | reviewer availability | Frozen IDs/ranks preserved and adjudication manifest hashes verified | BLOCKED_HUMAN_ACTION |
| B-FREE-REPLICATION-V1 | Critical | Scientific validity | Free Replication V1 manifest remains `PREPARING` with zero observations/calls; preflight and harness tests pass | Approve and execute frozen 200-case protocol | Researcher | Groq access/quota, preflight | 200 accounted cases, immutable model/protocol, reconciled ledger | BLOCKED_RESEARCHER_DECISION |
| B-COGNEE-COMPARISON | High | Scientific validity | Cognee Gate 5 produced empty graph/no live candidates; adapter contract remains testable but no valid ON comparison exists | Run isolated approved Cognee proof of concept | Researcher/admin | working Cognee environment, common corpus | non-empty cognify/search, provenance mapping, no cache substitution | BLOCKED_EXTERNAL_DEPENDENCY |
| B-CLAIM-EVIDENCE | High | Methodology and ground truth | Claim Verifier V2 deterministic tests pass, but approved complete labels and live E2E generation are absent; legacy heuristic audit remains superseded only for prototype status | Approve semantic benchmark labels and provider-backed E2E protocol, or formally authorize the existing V2 model path | Researcher | evidence references, adjudication, provider access | every measured claim tied to evidence and annotation status | BLOCKED_RESEARCHER_DECISION |
| B-LIVE-E2E-SECURITY | High | Researcher authorization | Deterministic security matrix/integrity tests pass; Phase 13D/Gate 6 live run remains stopped | Authorize frozen end-to-end evaluation | Researcher | provider access, frozen cases | case-family metrics and failure taxonomy recorded | BLOCKED_RESEARCHER_DECISION |
| BLK-007 | Medium | Documentation | Historical audit reports describe older pre-UI/pre-remediation state | Treat this status document and addenda as current source of truth | Maintainer | none | no conflicting “complete” claim remains in current status docs | ENGINEERING VERIFIED |
| BLK-008 | Medium | Engineering | Trust metadata was previously discarded and retrieved evidence injection was hardcoded clean | Preserve current remediation and regression coverage | Maintainer | focused tests | trust telemetry and evidence security state are traceable | ENGINEERING VERIFIED |
| BLK-009 | Medium | Research integrity | V3.1 strict audit rejects heuristic ground truth as independently verified | Keep the benchmark diagnostic-only until human review/adjudication exists | Researcher | reviewer availability | independent labels and integrity manifest pass without changing frozen inputs | BLOCKED BY MISSING GROUND TRUTH |

No blocker is marked complete merely because a report exists. Configuration,
authorization, ground truth, and scientific-validity blockers require the
specified external action and acceptance evidence.
