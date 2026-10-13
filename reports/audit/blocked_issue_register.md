# Blocked Issue Register

**Current revision:** `298593f115bee9ff4c0c2f075077bbe5e5da897d` plus current remediation changes

| ID | Severity | Type | Evidence | Required action | Owner | Dependencies | Acceptance criteria | Status |
|---|---|---|---|---|---|---|---|---|
| BLK-001 | Critical | Provider configuration | No supported live LLM/vision credentials configured | Configure authorized server-side credentials without committing secrets | Researcher/admin | quota, model access | Controlled synthetic image request completes or reports exact provider failure | BLOCKED BY CONFIGURATION |
| BLK-002 | Critical | Missing ground truth | Track A has frozen 530-position inputs but incomplete human labels | Complete researcher annotation/adjudication | Researcher | reviewer availability | Frozen IDs/ranks preserved and adjudication manifest hashes verified | BLOCKED BY MISSING GROUND TRUTH |
| BLK-003 | Critical | Scientific validity | Free Replication V1 manifest has zero observations/calls | Approve and execute frozen 200-case protocol | Researcher | Groq access/quota, preflight | 200 accounted cases, immutable model/protocol, reconciled ledger | BLOCKED BY RESEARCHER AUTHORIZATION |
| BLK-004 | High | Scientific validity | Cognee Gate 5 produced empty graph/no live candidates | Run isolated approved Cognee proof of concept | Researcher/admin | working Cognee environment, common corpus | non-empty cognify/search, provenance mapping, no cache substitution | BLOCKED BY RESOURCE |
| BLK-005 | High | Missing ground truth | Claim-evidence E2E benchmark has protocol/matrix but no approved complete labels | Import verified labels or obtain annotation | Researcher | evidence references, adjudication | every measured claim tied to evidence and annotation status | BLOCKED BY MISSING GROUND TRUTH |
| BLK-006 | High | Researcher authorization | Security Phase 13D/Gate 6 was stopped/blocked | Authorize frozen end-to-end evaluation | Researcher | provider access, frozen cases | case-family metrics and failure taxonomy recorded | BLOCKED BY RESEARCHER AUTHORIZATION |
| BLK-007 | Medium | Documentation | Historical audit reports describe older pre-UI/pre-remediation state | Treat this status document and addenda as current source of truth | Maintainer | none | no conflicting “complete” claim remains in current status docs | ENGINEERING VERIFIED |
| BLK-008 | Medium | Engineering | Trust metadata was previously discarded and retrieved evidence injection was hardcoded clean | Preserve current remediation and regression coverage | Maintainer | focused tests | trust telemetry and evidence security state are traceable | ENGINEERING VERIFIED |

No blocker is marked complete merely because a report exists. Configuration,
authorization, ground truth, and scientific-validity blockers require the
specified external action and acceptance evidence.
