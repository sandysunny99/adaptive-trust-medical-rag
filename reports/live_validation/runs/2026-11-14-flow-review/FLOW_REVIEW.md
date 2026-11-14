# Application flow review: 2026-11-14

- **Branch:** `wip/pre-threads-20261022-1440`, pushed to `claude/project-thread-cfap88`.
- **Base:** `2190fb0`.
- **Where:** the live app at http://localhost:5173 (Vite proxy to the FastAPI backend on 127.0.0.1:8000).
- **Browser:** Chrome, driven through Chrome DevTools.
- **Inputs:** synthetic only. The only image was `.playwright-mcp/fixtures/synthetic-rx.png`.

The screenshots (`01`–`11`, PNG, about 5 MB) are in this folder. They are not committed.

## Paths checked

| Path | Result |
|---|---|
| Landing page and "How it works" | OK |
| Empty input | OK: Analyze is disabled and a hint explains why |
| Invalid upload (`README.md`) | OK: an alert names the file and lists the allowed types |
| Typed pair: warfarin + ibuprofen | OK: safe abstention (no chunk has a verified source identity), R2, threshold 0.60 |
| Image upload | OK: Groq vision read Metformin and Amoxicillin (HIGH confidence) |
| Confirmation panel: edit, remove, add by hand | OK after fix 1. The edited and added names were the ones analysed. |
| Pipeline progress (SSE), result, evidence, excluded sources, security cards | OK |
| Prompt-injection note | OK: rejected with "did not pass security checks"; nothing reached the LLM |
| Cancel during a run | Missing; added (fix 2). Live check: the panel closes, Analyze is enabled again, and the backend drops the request (a later `/confirm` gets 404). |
| Save to History, then History view | OK: "Saved" state, list entry, detail view |
| About page | OK |
| 390 px phone width (Analyze, History, About, a result) | OK: no horizontal overflow |
| Backend unreachable (simulated in the page; servers left running) | Fails closed. The raw "Failed to fetch" message is replaced (fix 4). |
| Console errors | One misleading "SSE connection error" on every server-reported error (fix 3) |

## Fixes, each with a test

| Commit | Fix |
|---|---|
| `886b0b0` | Removed synchronous `setState` calls in effects (HistoryPage, WorkspacePage). oxlint now reports 0 warnings. |
| `12ecf69` | 1. The review panel's edit field and its icon-only Save and Cancel buttons had no accessible names. Enter now saves and Escape cancels. The add field also has a name now. |
| `142007a` | 2. Added a "Cancel analysis" button. The hook could already reset a run, but nothing in the UI called it, so the only way out was reloading the page. |
| `913f8cf` | 3. The backend's `event: error` also reaches `EventSource.onerror`. Every rejected run logged a false "connection error" and called `onError` a second time. |
| `2f3fc6b` | 4. When the backend is unreachable, the page now says so and asks you to check it, instead of showing the browser's raw "Failed to fetch". |
| `88346f6` | Test-only: the EventSource fake used a TypeScript parameter property, which this project's `erasableSyntaxOnly` setting forbids, so `tsc -b` failed. |

## Checks after the fixes

| Check | Result |
|---|---|
| Backend tests (`TESTING=1`, live-provider tests excluded) | 1899 passed, 1 xfail, 0 failed (unchanged) |
| ruff | Clean |
| bandit | No medium or high findings |
| Frontend tests | 150 of 150 passed (was 145; 5 new tests) |
| `npm run build` | Passes |
| oxlint | 0 warnings (was 3) |
| gitleaks on the new commits | Clean |

## Not changed, with reasons

- **`/health` reports "unhealthy".** It reports the research Postgres database, which the live app doesn't use. This is a documented decision from the 2026-10-26 audit, and `tests/test_api.py::test_health_status_unhealthy_without_db` pins it. `/health/ready` is the live readiness check, and the UI never calls `/health`.
- **`CLOUDFLARE_ENABLED=false` is ignored.** Cloudflare is used whenever its credentials are set, and the startup log says so. Routing is the owner's decision.
- **Food & Diet Guidance card.** It still shows on this branch; whether to keep it is the owner's decision.
- **Abstention on every pair.** The live corpus (`LIVE_MEDICAL_CORPUS_V2`, 14 chunks) has no chunks with a verified source identity for these pairs. This is a gap in the evidence corpus, not a code bug. Adding or approving sources is a research decision.
- **Chrome's "form field should have an id or name" notice.** This is an autofill hint only. Labels are present.
