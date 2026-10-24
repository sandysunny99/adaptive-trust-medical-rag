# Cancellation lifecycle, OCR process, deployment, provider/NLI validation and claim-strength UX (2026-10-23)

Research prototype, not a clinical tool, not production-ready, and no medical evidence was approved.

- **Worktree and state:** a separate worktree of branch `feature/multi-dataset-v2-evidence`, HEAD `395c214`. Nothing committed, staged or pushed.
- **Data:** synthetic images and drug names only.
- **Secrets:** keys were held in process memory and never printed.

Follows an earlier session report of the same day (cancellation hardening, kept locally), which reported 1,744 backend and 140 frontend tests passing. No file changed between that report and the start of this pass (checked by modification time), so it is this pass's baseline.

## 1. The six issues

| # | Issue | Status | Evidence |
|---|---|---|---|
| 1 | Cancel offered throughout the image lifecycle | **Fixed, verified** | "Cancel analysis" shows from the request ID until confirmation (OCR, vision, review); 5 new component tests; browser scenarios S1–S3 |
| 2 | Interrupt the real OCR process | **Fixed, verified** | OCR is now a `Popen` polled every 0.1 s and killed on a stop request; tests use a real child process; browser S1: `OCR process stopped (exit code 1)`, the process has exited |
| 3 | Unacknowledged cancel / stream disconnect / stranded requests | **Fixed, verified (process-local)** | Disconnect ends the request (real-uvicorn tests and browser S4, S5); new 120 s deadline for never-streamed uploads (tests and browser S6); retry alert reconciles |
| 4 | Real Groq vision and real PubMedBERT NLI | **Validated** | Real Groq: direct call and real-pipeline fallback, both grounded. Real NLI: 141 passed with the real model |
| 5 | Single-worker limitation | **Resolved as Option A (explicit single worker)** | Documented `--workers 1`; startup guard; real launch tests: 1 worker serves, 2 workers refuse to start |
| 6 | `strength_check` reasons in the UI | **Fixed, verified** | New `strength_code` / `strength_details`; plain-language reasons in the abstention status; 12 new component tests; browser S10, S11 |

## 2. Code paths changed

**Issue 1, frontend lifecycle.**
- `useAnalysis.ts`:
  - `abandonable` is true from the moment the request ID is known until confirmation, in the stages `uploading`, `extracting` and `confirming`.
  - `abandon()` is single-flight: every control shares one in-flight promise.
  - `confirm()` refuses while a cancel is in progress.
- `WorkspacePage.tsx`:
  - The "Cancel analysis" button sits in the form's action row, beside "Analyzing…", so it stays visible from extraction through review.
  - `cancelImageAnalysis` runs both this button and the panel's "Cancel and upload a different image".
  - The states are `cancelling` (button "Cancelling…", disabled) and `cancelled` (`role="status"`: "The image analysis was cancelled; nothing from it was analysed. Upload another image or enter medications by hand.").
  - The status is cleared on the next submission, and focus returns to the upload control.
  - The existing generation counter still drops every later event of the abandoned request.

**Issue 2, `services/image_grounding.py`.**
- `recognize_image_text(image_bytes, mime, stop=None)`:
  - It starts the same fixed absolute `powershell.exe` with the same fixed `-EncodedCommand` script and the same minimal environment (no keys). The image is in a private `TemporaryDirectory`.
  - `communicate(timeout=0.1)` is polled.
  - On a stop request, or past `OCR_TIMEOUT_S` (30 s, unchanged), the process is killed and reaped (`_end`) before the temporary directory is removed.
  - A stop returns the new status `STOPPED`, not `ERROR`. A stop set before the start starts no process.
  - A cleanup failure logs only the exception type.
- `services/live_application.py`:
  - The real OCR receives a `threading.Event`.
  - `_unless_cancelled(work, state, stop=...)` calls `stop` on a cancel and awaits the thread's exit (at most 5 s). It also calls it in `finally`, so a client disconnect stops the process too.
  - An injected recognizer (tests) cannot be stopped, and its result is dropped.

**Issue 3, `api/routes/analyze.py`.**
- **Disconnect:**
  - `pipeline_stream` handles the stream's own cancellation (Starlette cancels it on `http.disconnect`). It marks the request `cancelled` and `finished`, logs "Stream for … closed by the client; the analysis was stopped", and re-raises.
  - The existing `finally` drops the entry and the image.
- **Never-streamed uploads:**
  - Each submission gets `open_by = time.monotonic() + STREAM_OPEN_TTL_S` (120 s).
  - `_drop_unopened` runs on every new submission and drops expired, never-streamed entries, image included. **[Corrected in the addendum, A1: on an idle server nothing ran it, so an expired upload stayed in memory until another request arrived. Replaced by a per-request deadline timer.]**
  - A stream opened after its deadline gets `REQUEST_EXPIRED` and the entry is dropped.
- **Unchanged:** the 300 s confirmation deadline and the OCR/vision deadlines.

**Issue 5, `api/app.py`.**
- `requested_workers(argv, env)` reads `--workers N` / `--workers=N`, else `WEB_CONCURRENCY`, which is the order uvicorn uses.
- The lifespan refuses to start when that number is above 1.
- `README.md` and `docs/CONFIGURATION.md` now give `--workers 1` and the reason.

**Issue 6.**
- `services/claim_strength.py`:
  - `strength_issue()` returns a `StrengthIssue(code, message, details)`. It replaces `strength_violation()`, whose only other users were tests.
  - The codes are `ACTION_TOO_STRONG`, `UNSUPPORTED_DETAIL`, `NO_REVIEWED_RELATIONSHIP_WORDING` and `NO_REVIEWED_FOOD_WORDING`.
- `live_application.py` adds `strength_code` and `strength_details` to the withheld claim. The `strength_check` string is unchanged, so the API stays backward compatible.
- `types/index.ts` adds both fields as optional.
- `ResultPanel.tsx` maps each code to plain words, inside the existing single `role="status"` abstention block. Each reason appears once, and only for an abstention. It adds "Withheld claims are not shown. Their absence does not mean the medicines are safe together."
- An unknown code shows a generic line. Raw codes, actions, level numbers and the withheld sentence are never shown.

## 3. Cancellation and OCR-process guarantees

**Guaranteed, within this process:**
- **Before or during OCR:**
  - The OCR process is killed and has exited before the request reports `ANALYSIS_CANCELLED`, about 0.1–0.2 s after the stop. Its temporary image is removed, and no vision call is made.
  - Evidence: the process's own exit, both in tests (`proc.poll()` is not `None`) and in the browser (`OCR process stopped (exit code 1)`, process gone).
- **During a vision request:**
  - The httpx request is cancelled, and its client and connection are closed before the request ends.
  - No retry or fallback starts after the cancel; a real timeout still falls back to Groq.
  - A late answer is dropped.
- **While waiting for confirmation:** the wait is released at once, and no RxNorm, retrieval, relationship, LLM, claim-verification or safety-gate stage runs.
- **Cancel and confirm:** exactly one wins.

**Not guaranteed:**
- **Provider-side work:** a provider that already received the image may still process it.
- **Disconnect cleanup is not awaited:** after a disconnect, the OCR kill is signalled at once and happens within about 0.1 s, but nothing waits for it. The framework has cancelled the stream task, so nothing can await cleanup there. **[Corrected in the addendum, A2: the request used to be removed before its OCR process exited or its vision client closed. The cleanup is now awaited inside an anyio shield (bounded at 5 s), so it can be.]**

## 4. Stream disconnect and request lifetime

- **Disconnect:**
  - uvicorn 0.54 (h11) reports ASGI spec 2.3, so Starlette 1.6 listens for `http.disconnect` while the stream is idle and cancels it.
  - Proven against a real uvicorn server, with no cancel request at all:
    - while waiting for confirmation, the entry is gone in under 5 s, and a late confirm and a late cancel get 404;
    - while OCR runs, the child process is killed and its image removed.
  - Browser S4 and S5 show the same through the Vite proxy.
  - **Limit:** an ASGI server that reports spec 2.4 is not covered. Starlette then detects a disconnect only on the next send, and the deadlines below still bound the request. The real-uvicorn test will fail if a dependency upgrade changes this.
- **Upper bounds for a stranded request** (a partition that hides both the cancel and the disconnect):
  - never streamed: dropped 120 s after submission, at the next submission, or when its stream is opened; **[Overstated; corrected in the addendum, A1: before the fix it was dropped only at the next submission or when its stream was opened. It is now dropped by its own timer at 120 s.]**
  - streamed image request: at most about 30 s OCR, plus 75 s vision deadline, plus the 300 s confirmation deadline, so about 7 minutes. The page's alert states this bound.
  - After either, confirm and cancel get 404 and the stream gets `NOT_FOUND` or `REQUEST_EXPIRED`. Expiry is logged without content.
- **Process-local:** all of this holds only within the one worker that owns the request (section 5). No distributed cancellation is claimed.

## 5. Deployment model: one worker (Option A)

- **What exists:** the documented product is one local uvicorn process plus Vite. Docker Compose holds PostgreSQL/pgvector, but no shared request store. Adding Redis or a database-backed request registry (Option B) would be a separate architectural change, and the documented local deployment does not need it.
- **What was done:**
  - the documented command now ends with `--workers 1`;
  - the API refuses to start when uvicorn is asked for more workers through `--workers` or `WEB_CONCURRENCY`.
- **Verified by real launches of the documented command:**
  - with `--workers 1` it serves `/health`;
  - with `--workers 2` every worker raises "supports one worker; it was started with 2", and uvicorn stops the parent ("failed to start, stopping the parent process"). The parent's exit code is 0, which is uvicorn's own behaviour.
- **Limit:** `uvicorn.run(app, workers=N)` called from code, or another server's own worker option, is invisible to the guard. It is marked `shortcut:` in the code.

## 6. Real provider and real NLI results

**Real Groq vision.** Script `groq_vision_smoke.py` (kept outside the repository), synthetic `two_meds.png`, keys from local env files held in process memory only.
- **A, direct call to the configured Groq client** (`groq_vision`, model `qwen/qwen3.8-27b`):
  - local OCR read 92 characters;
  - Groq answered in 1.0 s, suggesting 2 names, both found in the image text, 0 withheld (warfarin, ibuprofen).
- **B, the real routes and pipeline**, with only NVIDIA's network send forced to time out (request `85133ac3`):
  - hosts contacted: `integrate.api.nvidia.com` (forced timeout), then `api.groq.com`;
  - attempts: `nvidia_vision` failed with TIMEOUT, `groq_vision` succeeded;
  - candidates: both `DETECTED` with image-text evidence, and the request waited for explicit confirmation;
  - the cancel then got 200 and `ANALYSIS_CANCELLED`, so nothing was analysed.
- **Not covered here:** a Groq answer that needed withholding. Both of Groq's names were genuinely printed. The withholding rule for Groq is covered by the stubbed NVIDIA→Groq chain test.

**Real PubMedBERT NLI** (`TESTING` unset).
- The verifier loaded a transformers `TextClassificationPipeline` over `BertForSequenceClassification` `pritamdeka/PubMedBERT-MNLI-MedNLI` at revision `f1b6ce2e…`, not the stand-in. The model loader printed its usual note about unexpected weight keys.
- `pytest tests/e2e/test_live_warfarin_ibuprofen.py tests/e2e/test_live_evidence_provenance.py tests/test_claim_strength.py tests/test_canonical_identity.py tests/e2e/test_live_relationship_evidence_v2.py`: exit 0, **141 passed**, 4 min 20 s.

**What the real model shows** (scored with `score_wordings.py` against the test-only approved REL-LIVE-0003 label chunk):

| Generated wording | Real entailment | Outcome |
|---|---|---|
| "…can increase the risk of hyperkalemia, so do not take them together [Source 1]." | 0.998 | withheld: `ACTION_TOO_STRONG` (AVOID) |
| "…; monitor potassium daily [Source 1]." | 1.0 | withheld: `UNSUPPORTED_DETAIL` (QUANTITY) |
| "…can definitely increase…" | 0.065 | withheld by NLI (no strength code) |

The real NLI entails an instruction to avoid a combination the source only lists as a risk. That is why the reviewed-wording check exists, and here it catches it.

## 7. Reason codes and UI messages

| `strength_code` | UI message |
|---|---|
| `ACTION_TOO_STRONG` | A statement was worded more strongly than the reviewed wording of its source supports. |
| `UNSUPPORTED_DETAIL` | A statement added {an amount or frequency / a timing / a certainty} that its source's reviewed wording does not state. |
| `NO_REVIEWED_RELATIONSHIP_WORDING` | No reviewed statement is available for this medication relationship, so no claim about it could be released. |
| `NO_REVIEWED_FOOD_WORDING` | No reviewed statement is available for this food or drink guidance, so it could not be released. |
| any other | A statement could not be verified against its source's reviewed wording. |

- **Other reasons keep their own messages.** No eligible evidence, unverified source identity, no approved relationship record and verification errors still show the backend's `abstention_reason`, with no wording list. Tests use the backend's real strings.
- **Label change from the browser run:** "an amount" became "an amount or frequency", because the backend's QUANTITY cue also matches "daily" and "per day".

## 8. Test results

All commands ran in the feature worktree. Backend commands used `uv run --frozen --offline`, with `TESTING=1` unless noted.

| # | Step | Command | Exit | Result | Time | Kind |
|---|---|---|---|---|---|---|
| 0 | Baseline | previous report; no file changed since (mtime check) | — | 1,744 backend + 4 skipped; 140 frontend | — | carried over |
| — | Red checks before fixes | the expiry tests; the deployment tests before the guard | 1 / 2 | failed as expected (no deadline; no guard) | — | deterministic |
| 1 | Cancellation, lifecycle, TTL, disconnect | `pytest tests/e2e/test_confirmation_state_machine.py` | 0 | 26 passed | 57 s | deterministic, plus real uvicorn sockets and a real child process |
| 2 | OCR process | `pytest tests/test_image_grounding.py` | 0 | 32 passed, including the real Windows OCR on synthetic images | 4 s | real child processes, real local OCR |
| 3 | Provider fallback/cancel + pipeline | `pytest tests/providers/test_vision_fallback_and_timeouts.py tests/e2e/test_image_grounding_pipeline.py` | 0 | 58 passed | 57 s | stubbed NVIDIA→Groq and an httpx transport |
| 4 | Lifecycle and TTL | included in step 1 | — | — | — | — |
| 5 | Deployment | `pytest tests/test_single_worker_deployment.py` | 0 | 8 passed (2 real uvicorn launches) | 8 s | real processes |
| 6 | Claim strength and API/SSE | `pytest tests/test_claim_strength.py tests/e2e/test_live_evidence_provenance.py tests/e2e/test_live_warfarin_ibuprofen.py` / `pytest tests/test_api.py tests/api tests/test_confirm_contract.py tests/e2e/test_v6_c6_… tests/e2e/test_v6_c10_…` | 0 / 0 | 63 / 85 passed | 48 s / 56 s | deterministic |
| 7 | Real Groq vision | `groq_vision_smoke.py two_meds.png` (`TESTING` unset) | 0 | A and B as in section 6 | 26 s | **real Groq**, stubbed NVIDIA timeout |
| 8 | Real PubMedBERT NLI | `pytest` on 5 files (section 6), `TESTING` unset | 0 | 141 passed | 4 min 20 s | **real NLI** |
| 9 | Full backend | `pytest -q` | 0 | **1,761 passed, 4 skipped** (live-credential tests), 0 failed | 3 min 54 s | deterministic |
| 10 | Full frontend | `vitest run` | 0 | **19 files, 155 passed** | 31 s | jsdom |
| 11 | TypeScript | `tsc -b --noEmit` | 0 | clean | 7 s | — |
| 12 | Build / lint | `npm run build` / `npm run lint` (oxlint) | 0 / 0 | built; 3 warnings, all present before this pass (`HistoryPage.tsx:41`, `WorkspacePage.tsx:58`, `WorkspacePage.tsx:98`, moved by added lines) | 5 s / 1 s | — |
| 13 | Ruff | `ruff check src tests scripts/build_*_candidate.py` | 0 | all checks passed | — | — |
| 14 | Bandit | `bandit -r src` | 1 | Low 13, Medium 0, High 0, unchanged. Exit 1 only for the Low findings. The OCR suppressions (`B404` import, `B603` now on the `Popen` line) still cover the fixed command, and no new finding appeared | — | — |
| 15 | Diff whitespace | `git diff --check` + scan of untracked files | 0 | clean | — | — |
| 16 | Gitleaks | `gitleaks git --pre-commit --staged=false`; `gitleaks dir` over every untracked file | 0 / 0 | no leaks | — | — |

New tests in this pass: 17 backend (1,744 → 1,761) and 15 frontend (140 → 155). One existing frontend test changed, because two cancel controls now both show "Cancelling…". Three existing OCR tests now fake `Popen` instead of `run`; the `TimeoutExpired` case moved to a test with a real process.

## 9. Browser and HTTP evidence

These runs used only an isolated local instance of the feature branch (its own backend, Vite dev server and synthetic-image server, bound to 127.0.0.1), separate from any other running instance.

The artifacts (filtered log lines with no keys and no OCR text, and screenshots) were kept locally and are not in the repository; the request IDs below refer to them.

| # | Scenario | Mode / input | Request | Result | Artifact |
|---|---|---|---|---|---|
| S1 | UI cancel during local OCR, before candidates | `slowocr`, image | b7fd2e29 | "Cancel analysis" shown beside "Analyzing…", with no candidate panel. Cancel 200; `OCR process stopped (exit code 1)`; the OCR process exited; vision never called; status "…was cancelled; nothing from it was analysed…"; focus on "Replace image" | `S1_cancel_analysis_offered_while_ocr_runs.jpg`, `demo_slowocr_lines.txt` |
| S2/S3 | UI cancel during a delayed httpx vision request | `slowvision`, image | 16b9929e | Real OCR read 92 characters; 28,647-byte request reached the silent provider; UI cancel; the provider saw the client close after 9.7 s; cancel 200; "cancelled during extraction… no other provider is tried"; no fallback | `demo_slowvision_lines.txt` |
| S4 | Cancel endpoint unreachable | `slowocr`, image, page's cancel POST made to fail | 075359e1 | Alert "The server did not confirm…" with "Retry cancellation", and no success text. With no cancel at all, the page's stream close ended the request on the server ("Stream for … closed by the client"); OCR killed (the process exited). Network restored, then Retry: server 404, so status "The earlier image analysis has ended on the server."; focus on "Replace image" | `demo_slowocr_lines.txt` |
| S5 | Page reload during the vision request | `slowvision`, image | faa92ee3 | "Stream … closed by the client"; the provider saw the close after 7.5 s; late confirm 404 | `demo_slowvision_lines.txt` |
| S6 | Request expiry and a stale confirmation | `slowvision`, upload with curl, stream never opened | b7b93e62 | After 125 s: stream `REQUEST_EXPIRED`; "expired before its stream opened; dropped"; late confirm 404, late cancel 404 | `demo_slowvision_lines.txt` |
| S7 | Real Groq extraction | script through the real routes (not the browser) | 85133ac3 | See section 6 | `groq_smoke_lines.txt` |
| S8 | Verified relationship reaches Relationship Verification | `relationship`, Lisinopril + Spironolactone, supported wording | cdeabcb8, 6b0f03ff | Released, through Relationship Verification, Claim Verification (real PubMedBERT) and Safety Gate; 1 evidence item | `demo_relationship_run1_lines.txt`, `demo_relationship_lines.txt` |
| S9 | Missing eligible source abstains before generation | `real` (unmodified live app), Warfarin + Ibuprofen | e28ac1c7 | Abstained: "2 evidence chunk(s)… none has a verified source identity…"; 0 LLM provider requests; no wording list | `demo_real_lines.txt` |
| S10 | Claim-strength failure explained | `relationship`, rotated wordings | f1b2d461, 5103322e | f1b2d461: "A statement was worded more strongly than the reviewed wording of its source supports." 5103322e: the added-detail message. The withheld sentence was never shown; one status region. An earlier run (55c598c6, "will always") was withheld by NLI and correctly showed no wording reason | `S10_action_too_strong_reason_in_abstention.jpg`, `demo_relationship_lines.txt` |
| S11 | A new request clears the old progress and reasons | `relationship`, third run | 6b0f03ff | Released; no earlier reason or conclusion remains | `demo_relationship_lines.txt` |

The browser pane was hidden during the runs, so `requestAnimationFrame` (the focus move) ran late and one screenshot was stale. The states were read from the DOM.

## 10. Final state

- **Worktree.** Branch `feature/multi-dataset-v2-evidence`, HEAD `395c214`, 0 staged, 0 new commits. Across all passes on this branch: 52 modified tracked files and 36 untracked, this report included. This pass touched the 20 files in section 2 and the two docs, plus this report.
- **`data/`.** `git diff 395c214 -- data/` is empty, and no v2 folder exists in `data/live_medical/relationships/`.
- **Original checkout.** Branch `wip/pre-threads-20261022-1440`, HEAD `a96e171`, 0 staged; this pass wrote nothing there.
- **Frozen commits intact:** `baf6c93d066fbdb6b0c8a698fd878294ddd9f8bd`, `30774ebe78a3b320bc8b2b954ceebc58e031e564`.
- **`.env.local`.** Not modified or copied, untracked, and absent from the worktree. Keys were only loaded into process memory by the scratch launchers.
- **Live data.** All 3 SHA-256 hashes in the original checkout match the baseline: `LIVE_MEDICAL_CORPUS_V2.json`, `LIVE_RELATIONSHIP_RECORDS_V1.json`, `LIVE_RELATIONSHIP_RECORDS_V1_MANIFEST.json`.
- **Candidates.**
  - FOOD-0001, REL-LIVE-0003 and REL-LIVE-0004 are `CANDIDATE_PENDING_RESEARCHER_APPROVAL`; REL-LIVE-0003 and REL-LIVE-0004 have severity `UNGRADED`. Their files were last changed on 2026-10-22.
  - The browser runs' test-only approval lived only in a temporary folder outside the repository, which was deleted afterwards. No approval was copied into live storage.
- **Processes.** Every backend, frontend, image server and child started for this work is stopped, and pytest temporary folders were removed.
- **Git.** No commit, stage, push, tag, merge, deployment or activation.

## 11. Remaining blockers and human decisions

- **Commit decision.** Everything is uncommitted on the feature branch; the original checkout does not have it. A diff review and your commit decision are next.
- **Evidence approval.** This is a separate human step. FOOD-0001, REL-LIVE-0003 and REL-LIVE-0004 stay pending, and REL-LIVE-0003 and REL-LIVE-0004 stay UNGRADED. The S8/S10 runs used a test-only approval in a temporary folder outside the repository, which was deleted afterwards.
- **Multi-worker or multi-host deployment** needs a shared request store with atomic transitions (Option B). This was not built.
- **Image upload on non-Windows backends** is still unavailable (fail closed). Typed entry works.
- **A provider that already received an image** may still process it after a cancel.
- **Not run:**
  - a live cancel against the real NVIDIA or Groq endpoints (deliberately; see section 3);
  - a browser run of S7 (it went through the real routes by script);
  - an ASGI server reporting spec 2.4.

---

## Addendum: adversarial audit (2026-10-23, later the same day)

This addendum audits the report above against the code. Sections 1–11 are kept as written. The statements this audit found too broad are marked inline as corrected, and the corrections are given here. Nothing was committed, staged, pushed, tagged, merged or deployed, and no evidence was approved.

### A0. Baseline reconciliation

- At the start of the audit, only this report was newer than the recorded full backend run (21:34). The 1,761 / 155 / 141 results therefore described the code as it stood.
- No frontend file changed during the audit, so the frontend result (19 files, 155 passed) is **carried over, not re-run**.

### A1. Expired never-streamed uploads (defect, reproduced and fixed)

- **Defect.** On an idle server, an upload whose stream never opened stayed in memory, image included, after its 120 s deadline. Removal ran only on the next submission (`_drop_unopened`) or when that request's stream was opened. Section 2 and section 4 overstated this, and are marked.
- **Reproduction.** `test_an_unopened_upload_is_dropped_at_its_deadline_with_no_further_request`: deadline 0.2 s, then no request of any kind for 0.6 s. Before the fix: `assert (True and False)`; the entry was still there.
- **Fix** (`api/routes/analyze.py`):
  - **Per-request timer:** each submission goes through `_hold()`, which stores the entry and schedules `loop.call_later(STREAM_OPEN_TTL_S, _drop_if_unopened, pending, request_id)` on the server's monotonic loop clock. `_drop_unopened` was removed.
  - **What the timer drops:** only an entry still in the registry and not streaming. Removing it twice is harmless. The timer holds no reference to the entry, so it never keeps an image alive.
  - **Stream-start check:** the stream generator's first step checks that its entry is still registered, then marks it streaming, with no `await` in between. A timer that fires after the route's check but before the generator starts therefore produces `REQUEST_EXPIRED`, never an orphaned run.
  - **Late-timer guard:** the route keeps its own deadline check for a timer delayed on a busy loop.
- **Rejected alternative.** Marking `streaming` in the route was tried and reverted before any test run. A client that vanished before the body started would have left an entry marked streaming that no timer or generator would ever remove.
- **Tests.**
  - The idle test above also checks that, afterwards, no dict holds the upload's image bytes (`gc.get_referrers`), that the stream gets `NOT_FOUND`, and that confirm and cancel get 404.
  - `test_a_stream_opened_after_its_deadline_is_refused_even_if_its_timer_is_late`: the timer is disabled, and the route's guard returns `REQUEST_EXPIRED`.
  - `test_a_request_whose_stream_opened_in_time_is_not_touched_by_its_open_deadline`: a stream opened in time outlives its open deadline, and the confirmation runs exactly once.
- **Limits.**
  - The timer lives in process memory and on the server's loop. A restart loses timers and entries alike.
  - The image is freed by Python's garbage collector once the registry drops its reference. Memory use was not measured.
  - Request IDs are server-generated uuid4 values, so an ID is never reused. That is why the timer is keyed by ID and not by the entry object; keying by the entry would hold the image until the timer fires.

### A2. Disconnect cleanup ordering (defect, reproduced and fixed)

- **Defect.** On a client disconnect, the request was removed from the registry before its OCR process had exited and its image file had been deleted, or before its vision HTTP request had been interrupted and its client closed. Section 3 stated this as a limit; it is now fixed and marked.
- **Reproduction.**
  - `test_a_client_that_drops_its_stream_ends_the_request_after_its_own_work_is_stopped[ocr_running|vision_running]` runs against a real uvicorn server with real sockets.
  - The request registry is replaced by `RemovalProbe`, which records the state of the request's owned work at the moment the request is removed.
  - Before the fix: OCR `{'process_exited': False, 'image_removed': False}`, vision `{'request_interrupted': False, 'client_closed': False}`.
- **Root cause.** Starlette cancels a disconnected stream through an anyio cancel scope, and that cancellation repeats at every `await`. `_unless_cancelled` could therefore only *signal* the stop. The cancellation then reached `pipeline_stream`, which marked the request and removed it at once.
- **Fix** (`services/live_application.py`).
  - One path in `_unless_cancelled`'s `finally` serves an explicit cancel, a disconnect and an error:
    1. stop the work (OCR: set the stop event, so the thread kills and reaps its process and removes its temporary folder; vision: cancel the task, so httpx abandons the request and closes its client);
    2. wait for it inside `anyio.CancelScope(shield=True)`, bounded by `CANCEL_CLEANUP_S` (5 s);
    3. past the bound, log a warning ("did not stop within 5 s; its result is dropped") and abandon the work. A done-callback still collects its result or error.
  - `anyio` is imported directly. It is already installed as a dependency of Starlette and httpx but is not listed in `pyproject.toml`.
- **Order now**, as shown by the probe (all `True` at removal):
  1. disconnect;
  2. stop signal;
  3. OCR process exited and its image deleted, or the vision request interrupted and its client closed;
  4. request marked cancelled (`pipeline_stream`'s `except CancelledError`);
  5. registry entry removed (`finally`).
- **Explicit cancel route.** `POST /cancel` sets `cancelled`/`finished` immediately, so a late confirm is refused from that moment. The request is *removed* only after its cleanup, as above.
- **Tests.**
  - The probe test now has three cases: `awaiting_confirmation`, `ocr_running` and `vision_running`.
  - A deliberately failing cleanup: `test_work_that_will_not_stop_is_abandoned_at_the_bound_and_its_late_answer_dropped`, with the bound set to 0.3 s and a vision stub that ignores every cancel for 1.5 s and then answers. The request ends with `ANALYSIS_CANCELLED` within the bound, the warning is logged, and the late answer arrives but produces no candidates, no confirmation request and no downstream stage.
  - `test_a_failed_process_cleanup_is_logged_without_paths_or_data` (from the original pass) still covers a process that refuses to die.
- **Not applicable.** "Disconnect during expiry cleanup": a request that never streamed has no stream to disconnect, and a stream opened after expiry ends at once.
- **Limits.**
  - The shield blocks anyio cancellation, which is how Starlette cancels. A second native `Task.cancel()` arriving during the wait is not blocked; the wait is bounded either way.
  - A remote provider may keep processing an image it already received.

### A3. Worker-guard coverage (verified, with one unguarded path)

| Launch | Guard result | Evidence |
|---|---|---|
| Documented CLI with `--workers 1` | serves `/health` | `test_the_documented_single_worker_command_serves` |
| CLI with `--workers 2` | every worker refuses; uvicorn stops the parent | `test_the_same_command_with_two_workers_refuses_to_start[--workers 2]` |
| CLI without `--workers`, `WEB_CONCURRENCY=2` | refused | `…[WEB_CONCURRENCY=2]` (added in this audit) |
| `uvicorn.run(app_object, workers=2)` from code | refused by **uvicorn itself** (needs an import string for workers; exit 3), not by the guard | scratch probe `programmatic_workers.py object` |
| `uvicorn.run("adaptive_trust_medical_rag.api.app:app", workers=2)` from code | **not detected: two workers served `/health`** | scratch probe `programmatic_workers.py import-string`: a launcher, a uvicorn parent and two logged workers |
| gunicorn | not installed; not a supported launch | — |

- **Why the import-string path stays open.** The guard can see only `sys.argv` and `WEB_CONCURRENCY`. In a uvicorn worker, the worker count lives in uvicorn's own config object, which the application cannot reach without uvicorn internals. No script in the repository launches uvicorn from code. The supported contract is the documented CLI command; the code marks this limit as a `shortcut:`.
- **Process handling.** The probe was re-run and its own process tree was ended by its launcher's exact process ID. The first probe run had been cleaned up by command-line match, which also ended the shell running that probe; all later cleanup used exact process IDs. No unrelated process was stopped.

### A4. OCR process tree (verified on this machine)

- **Probe.** `ocr_process_tree.py` took Windows Toolhelp32 snapshots every 10 ms, recording real parent/child PIDs, across a full real read and a stop. The full read took 2.28 s and read 2,028 characters. The stop came at 0.8 s and returned `STOPPED` after 0.95 s.
- **Result.** PowerShell started **no** child process; WinRT OCR runs inside it. After the stop, the PowerShell PID was gone and no descendant remained.
- **New test.** `test_a_stop_request_ends_the_real_powershell_ocr_process` (Windows only; it ran and passed here) stops the real PowerShell OCR and checks that the process exited and its image was removed.
- **Limits.**
  - Two runs on one Windows build: a child living under 10 ms could be missed.
  - `kill()` ends one process. If a future OCR script started child processes, they would need a Job Object, which is not built.
- **Unchanged.** The fixed absolute `powershell.exe`, the fixed encoded script and the minimal environment without keys.

### A5. Provider and cancellation guarantees

- **Real Groq not re-run.** The success path (`return await task`) is the same code as before. The audit changed only the cancel, disconnect and error cleanup path, which the stubbed and transport-level tests re-ran: provider and pipeline 58 passed.
- **Real Groq result** (request 85133ac3, section 6) is therefore carried over from before the audit change.

### A6. Claim strength (re-audited, not modified)

- **Emission.** `strength_code` is set in exactly one place, and only on a claim the NLI supported. A claim that fails NLI is still withheld without a code, and the UI then shows only the backend's reason (browser run 55c598c6).
- **Backward compatibility.** `strength_check` is unchanged.
- **Gates.** Source identity, relationship approval and food-evidence separation are untouched. The claim-strength suites passed (63, and 141 with the real model).

### A7. Test configuration and harness audit

- **`tests/conftest.py`.**
  - The automatic fixtures set `LLM_MODE=DETERMINISTIC_MOCK` when unset (the LLM only) and replace the local OCR with a stand-in.
  - The NLI stand-in is chosen only by `TESTING=1` inside `ClaimVerifierV2.__init__`, and conftest never sets `TESTING`.
  - `endless_ocr_process` is opt-in, replaces only commands ending in `powershell.exe`, and kills its own children at teardown.
- **Proof the real model predicted.**
  - `nli_call_probe.py`, a pytest plugin, wraps `transformers.pipelines.text_classification.TextClassificationPipeline.__call__`. That method runs inference, not model construction.
  - The rerun counted **36 real calls** with `TESTING=None`. The wrapper only counts and passes every call through unchanged.
- **Scratch tools.** All untracked and outside the repository: `groq_vision_smoke.py`, `launch_feature_backend_demo.py`, `programmatic_workers.py`, `ocr_process_tree.py`, `nli_call_probe.py`, `score_wordings.py`, `bandit_compare.py`. They use synthetic inputs and hold keys only in process memory. The demo launcher binds 127.0.0.1 only, and its test-only approval lived in a temporary folder outside the repository, deleted after use.
- **Exit codes.** Each pytest run's output went to its own log, and the exit code recorded was pytest's own (`$?` or `PIPESTATUS[0]`), never that of a later formatting command.

### A8. Results of this audit

| Step | Command | Exit | Result | Kind |
|---|---|---|---|---|
| Red: A1, A2 | `pytest … -k "no_further_request or own_work"` | 1 | 3 failed as expected (idle expiry; OCR and vision cleanup order) | real uvicorn and child processes |
| Lifecycle | `pytest tests/e2e/test_confirmation_state_machine.py` | 0 | 29 passed | deterministic, real sockets, real child process |
| OCR | `pytest tests/test_image_grounding.py` | 0 | 33 passed, including real PowerShell OCR and the real stop | real local OCR |
| Deployment | `pytest tests/test_single_worker_deployment.py` | 0 | 9 passed (3 real launches) | real processes |
| Provider and pipeline / claim strength / API and SSE | focused `pytest` runs | 0 / 0 / 0 | 58 / 63 / 85 passed | deterministic |
| Real PubMedBERT | `pytest` on the 5 files, `TESTING` unset, `-p nli_call_probe` | 0 | **141 passed**, 36 real pipeline calls, 4 min 55 s | **real NLI** |
| Full backend (after the code fixes) | `pytest -q` | 0 | 1,764 passed, 4 skipped | deterministic |
| Full backend (final, with the audit tests added after it) | `pytest -q` | 0 | **1,766 passed, 4 skipped**, 0 failed, 6 min 21 s (1,764 plus the 2 lifecycle tests added after that run) | deterministic |
| Full frontend, TypeScript, build, lint | — | — | carried over (no frontend change): 155 passed; clean; built; 3 warnings present before this pass | — |
| Ruff | `ruff check src tests scripts/build_*_candidate.py` | 0 | all checks passed | — |
| Bandit, full | `bandit -r src` | **1** | 13 Low, 0 Medium, 0 High. **Identical** finding by finding to `src` at `395c214` (`git archive` export, `bandit_compare.py`), all in files this branch never touched | — |
| Bandit, Medium and above | `bandit -r src -ll` | 0 | no findings | — |
| Diff whitespace | `git diff --check` + scan of untracked files | 0 | clean | — |
| Gitleaks | diff; all untracked files; audit scripts and logs | 0 / 0 / 0 | no leaks | — |

### A9. Final state

- **Worktree.** Branch `feature/multi-dataset-v2-evidence`, HEAD `395c214`, 0 staged, 0 new commits; 52 modified tracked and 36 untracked files.
- **This audit's changes.**
  - `src/adaptive_trust_medical_rag/api/routes/analyze.py`: deadline timer and stream-start check.
  - `src/adaptive_trust_medical_rag/services/live_application.py`: shielded, bounded cleanup.
  - `tests/e2e/test_confirmation_state_machine.py`, `tests/test_image_grounding.py`, `tests/test_single_worker_deployment.py`.
  - This report.
- **`data/`.** `git diff 395c214 -- data/` is empty, and no v2 relationship folder exists.
- **Original checkout.** `wip/pre-threads-20261022-1440` at `a96e171`, 0 staged; this audit wrote nothing there.
- **Frozen commits intact:** `baf6c93d066fbdb6b0c8a698fd878294ddd9f8bd`, `30774ebe78a3b320bc8b2b954ceebc58e031e564`.
- **`.env.local`.** Not modified or copied, untracked, and absent from the worktree.
- **Live data.** All 3 SHA-256 hashes match the baseline.
- **Candidates.** FOOD-0001, REL-LIVE-0003 and REL-LIVE-0004 are `CANDIDATE_PENDING_RESEARCHER_APPROVAL`; REL-LIVE-0003 and REL-LIVE-0004 have severity `UNGRADED`. Their files were last changed on 2026-10-22, and no approval exists in live storage.
- **Processes.** All probes and servers started for this audit are stopped.

### A10. Remaining limits needing a decision

1. **One worker only.** Requests, deadlines and cancellation are process-local. Multiple workers or hosts need a shared request store with atomic transitions. This was not built.
2. **Programmatic launches.** `uvicorn.run("…:app", workers=N)` from code is not detected. Use the documented CLI command.
3. **Cleanup bound.** Cleanup is awaited for up to 5 s; work still running after that is abandoned with a warning, and its result is dropped.
4. **Provider-side work.** A provider may keep processing an image it already received.
5. **OCR process tree.** No children were observed on this Windows build. Child processes, if a future script ever starts them, are not covered.
6. **ASGI spec 2.4 servers.** They detect a disconnect only on the next send. The deadlines still bound the request.
7. **`anyio` dependency.** It is used directly but is only a transitive dependency. Whether to list it in `pyproject.toml` is a packaging decision, left to you because it changes `uv.lock`.
8. **Commit and evidence decisions.** The diff review and your commit decision come next. Evidence approval stays a separate human step.

This is not production-ready and not clinically validated.

---

## Final section: dependency declaration and closing verification (2026-10-23)

### D1. `anyio` declared as a direct runtime dependency (resolves A10, item 7)

- **Why.** `services/live_application.py` imports `anyio` and calls `anyio.CancelScope(shield=True)` in production code. It was only present because Starlette and httpx depend on it.
- **Change.** Made with the project's own workflow: `uv add "anyio>=4.14.2" --no-sync --offline` (uv 0.12.5). The floor is the version already locked, following the existing `name>=<locked version>` convention.
- **`pyproject.toml`:** one line added to `[project] dependencies`, not to a dev or optional group:

  ```
  +    "anyio>=4.14.2",
  ```
- **`uv.lock`:** two lines added, both in the root package's own entries. No package version changed; the lock still resolves 162 packages, with `anyio` 4.14.2, Starlette 1.6.0, httpx 0.28.1, FastAPI 0.141.1 and uvicorn 0.54.0:

  ```
  +    { name = "anyio" },                              # the project's dependencies
  +    { name = "anyio", specifier = ">=4.14.2" },      # the project's requires-dist
  ```
- **Line endings.** uv wrote both files with LF line endings; they were put back to CRLF, as checked out, so the working copy changes only these lines.
- **Checks.**

| Check | Command | Exit | Result |
|---|---|---|---|
| Lock up to date, before | `uv lock --check --offline` | 0 | resolved 162 packages |
| Lock up to date, after | `uv lock --check --offline` | 0 | resolved 162 packages |
| Locked environment | `uv sync --locked --offline --dry-run` | 0 | "Would make no changes" (142 installed packages checked). The project is not packaged, so uv warns that it skips entry points; this is unchanged |
| Frozen offline import | `PYTHONPATH=src uv run --frozen --offline python -c "import anyio; … import app"` | 0 | `anyio` 4.14.2, the app imports, `anyio.CancelScope` present. Without `PYTHONPATH=src` the import fails, because the project runs from `src/` (the documented command uses `--app-dir src`); this is unchanged |

### D2. Regression after the dependency change

No installed package changed (the dry run above), and no Python or frontend source changed after the 1,766-test full backend run and the 155-test frontend run (checked by modification time). So the suites that exercise the changed cancellation path were re-run against the final dependency state, rather than the full suites:

| Suite | Command | Exit | Result | Kind |
|---|---|---|---|---|
| Lifecycle, cancel, expiry, disconnect | `pytest tests/e2e/test_confirmation_state_machine.py` | 0 | 29 passed | real uvicorn sockets, real child processes, deterministic stubs |
| OCR | `pytest tests/test_image_grounding.py` | 0 | 33 passed | real Windows OCR, real PowerShell stop, real child processes |
| Deployment | `pytest tests/test_single_worker_deployment.py` | 0 | 9 passed | 3 real uvicorn launches |
| API and SSE | `pytest tests/test_api.py tests/api tests/test_confirm_contract.py tests/e2e/test_v6_c6_… tests/e2e/test_v6_c10_…` | 0 | 85 passed | deterministic |

**Carried over** (no runtime package or source change since they ran):

| Result | Kind |
|---|---|
| Full backend: 1,766 passed, 4 skipped, exit 0 | deterministic |
| Frontend: 155 passed; TypeScript; build; lint (3 warnings present before this work) | jsdom |
| Real PubMedBERT: 141 passed, 36 real inference calls | **real NLI** |
| Real Groq smoke (request 85133ac3) | **real Groq**; NVIDIA timeout forced, Groq call real |
| Browser S1–S11 | real browser, isolated app |

### D3. Static and security, against the final diff

| Check | Exit | Result |
|---|---|---|
| Ruff (`src tests scripts/build_*_candidate.py`) | 0 | all checks passed |
| `git diff --check` + scan of untracked files | 0 | clean |
| Gitleaks: diff (now including `pyproject.toml` and `uv.lock`); all untracked files | 0 / 0 | no leaks |
| Bandit | — | not re-run: no Python source changed since A8, where the full scan exited **1** (13 Low, 0 Medium, 0 High, identical to `395c214`) and `-ll` exited 0 |

### D4. Diff review of the whole branch (read-only)

- **Size.** 54 tracked files changed against `395c214` (2,880 insertions, 463 deletions), plus 36 untracked files.
- **Untracked files outside `tests/` and `reports/`:**
  - `src/…/services/claim_strength.py` and `src/…/services/image_grounding.py`;
  - `frontend/src/services/evidenceDisplay.ts`;
  - the three `scripts/build_*_candidate.py` from the multi-dataset pass.
- **No scratch tools in the repository.** Smoke scripts, launchers and probes all live in a local folder outside the repository.
- **`data/`:** no change.
- **Safety thresholds.** `trust_scoring/trust_scorer.py` and `verification/claim_verifier_v2.py` are unchanged against `395c214`, and `TRUST_THRESHOLDS` is untouched.
- **Claim strength.** `strength_check` is unchanged; `strength_code` and `strength_details` are optional, and unknown codes get the generic message (D2 and section 7).
- **Added log lines.**
  - The lines from this hardening series log only IDs, statuses, counts, provider and model names, and exception types: no OCR text, image bytes, temporary paths or keys.
  - **Finding for your decision (from earlier passes):** two lines log a provider's *error body* to the server log only: `openai_compatible_backend.py:194` and `openai_vision_backend.py:442`. Both are capped in length, whitespace-collapsed, and redacted of secrets or the API key. Their own comments say a body "can echo input".
  - The project's privacy rule limits logs to hashes, IDs and scores, so logging only the body's length and the status would be stricter. Not changed here, because it alters existing diagnostics.
- **Line endings.** Many working-copy files have LF line endings where the checkout uses CRLF, including the tests from earlier passes. Git normalizes them, and `git diff` shows content changes only.

### D5. Final state

- **Worktree.** Branch `feature/multi-dataset-v2-evidence`, HEAD `395c214`, 0 staged, 0 new commits; 54 modified tracked files (the two dependency files added to the 52 before) and 36 untracked.
- **Original checkout.** `a96e171`, 0 staged; this step wrote nothing there.
- **Frozen commits intact:** `baf6c93d066fbdb6b0c8a698fd878294ddd9f8bd`, `30774ebe78a3b320bc8b2b954ceebc58e031e564`.
- **`.env.local`.** Not modified or copied, untracked.
- **Live data.** All 3 SHA-256 hashes match the baseline, and `git diff 395c214 -- data/` is empty.
- **Candidates.** FOOD-0001, REL-LIVE-0003 and REL-LIVE-0004 are `CANDIDATE_PENDING_RESEARCHER_APPROVAL`; REL-LIVE-0003 and REL-LIVE-0004 are `UNGRADED`. No approval exists in live storage.
- **Processes.** Only test processes ran in this step, and all have exited.
- **Git.** No commit, stage, push, tag, merge, deployment, evidence approval or activation.
- **Placeholders.** None remain in this report.

### D6. Still open

- **One worker only.** The documented CLI is the supported launch; `uvicorn.run("…:app", workers=N)` from code is not detected (A3).
- **Cleanup bound.** Work still running after 5 s is abandoned with a warning, and its result is dropped. It is not reported as stopped.
- **Provider-side work.** A provider may keep processing an image it already received.
- **Platforms.** Image OCR works only on Windows; other hosts fail closed and typed entry works. ASGI spec 2.4 servers are untested.
- **Provider error bodies in the server log** (D4): your decision. **[Resolved in E1: only the body's length is logged now.]**
- **Next human steps.** Diff review and your commit decision, then evidence approval as its own step.

---

## Closing section: privacy fix, candidate fixtures, documentation and publication (2026-10-24)

### E1. Provider error bodies are no longer logged (resolves D4)

- **Change.** `openai_compatible_backend.py` and `openai_vision_backend.py` still read an upstream error body, but only to classify the failure (schema, transient, authentication, model not found). The log line now carries provider or model, HTTP status, category and the body's **length** only. Truncating or redacting a body does not make it safe, because it can echo the prompt, the prescription text or the account.
- **Sentinel tests.** A synthetic sentinel string is placed in the upstream body and checked to be absent from the captured log (and, for the pipeline, from every event sent to the user):
  - LLM path: `test_an_upstream_error_body_is_classified_but_never_logged` for a 400 schema error, a 503 transient error and a 401 authentication error (with a fake key). Each is still classified correctly.
  - Vision path: `test_a_vision_error_body_is_never_logged` for 400, 404 and 503 (the 503 is retried once).
  - A 200 prose reply that quotes the prescription goes through the real client and the live service. It ends as `VISION_EXTRACTION_ERROR` / `SCHEMA_ERROR` (`test_a_reply_quoting_the_prescription_reaches_neither_the_log_nor_the_user`).
  - All 7 cases passed in the publishable tree (E4).

### E2. Pending candidate fixtures: kept local, not published

- **What depends on them.** These fixture folders hold verbatim DailyMed label sections with real set IDs: `tests/fixtures/{food_0001,rel_live_0003,rel_live_0004}_candidate/`, 9 files. All three manifests are `CANDIDATE_PENDING_RESEARCHER_APPROVAL`, and REL-LIVE-0003 and REL-LIVE-0004 are `UNGRADED`. The tests that need them were found empirically, by moving the folders away and running the suite. 46 test functions (56 cases) in four files depend on them.
- **Why not replace them with synthetic data.** Those tests check real-label behaviour: PubMedBERT entailment on real label wording, source identity records that resolve real set IDs, byte-exact evidence hashes and the multi-dataset loader over real datasets. Synthetic stand-ins would have meant rewriting all 46 and would test something weaker. So no synthetic replacement was made.
- **What was done instead.** Each of the four files was split by a script. The fixture-independent tests (42 cases) stay in the committed file. The dependent tests move, with the helpers only they use, to a local-only companion `*_candidates.py` that imports the shared helpers. Nothing was rewritten: test bodies are unchanged, and the four companions plus the main files pass together (98 cases) with the fixtures present. The main files pass alone (42 cases) with the fixtures removed. The three candidate build scripts are also kept local.
- **Not published:** the 9 fixture files, the 3 `scripts/build_*_candidate.py` files and the 4 `*_candidates.py` files. No candidate status was changed and nothing was approved or graded.
- **Candidate content check.** Two frontend tests used the real DailyMed set ID of a candidate's source label as a sample link. They now use a synthetic set ID; the assertions use the constant, so they are unchanged, and both still pass. A scan of every published file found none of the candidates' set IDs and no 60-character window of their evidence text.
- **Least risky ways forward:**
  1. A researcher reviews the candidates and decides whether they may be published as pending fixtures; the companions then merge back into their main files unchanged.
  2. A separate task builds clearly synthetic datasets and ports the 46 tests to them, with a review of what real-label coverage is lost.
  3. Keep the current split: the published suite covers everything except real-label candidate behaviour, which runs locally.

### E3. Documentation

- `README.md`, `docs/ARCHITECTURE.md`, `docs/CONFIGURATION.md` and `docs/TESTING.md` were updated to match the code: OCR-first image flow (Windows only, fail closed), grounding, the vision fallback chain and its variables, the confirm and cancel endpoints, the request lifecycle (120 s stream-open deadline, 300 s confirmation, 5 s cleanup bound, disconnect), the single-worker guard, the source identity and evidence states, claim strength, the real-NLI test command and the Bandit gate. The README carries no test counts.
- **Bandit, both ways.** `run_bandit.py` runs Bandit with the `.bandit` skip list and fails on any finding outside it: exit 0. Raw `bandit -r src` has no skip list and exits 1 on 13 Low findings, which are identical to `395c214`. Medium 0, High 0.
- Of the six session reports of 2026-10-23, only this one is published, with local paths, process IDs, ports, file timestamps and references to other sessions removed. The five earlier ones are superseded by it and stay local.

### E4. Fresh validation of the final tree

| Check | Tree | Exit | Result |
|---|---|---|---|
| Full backend, `TESTING=1` | development tree (with local candidate tests) | 0 | 1773 passed, 4 skipped, 0 failed |
| **Full backend, `TESTING=1`** | **publishable tree**: a fresh worktree of `395c214` plus exactly the committed files | 0 | **1717 passed, 4 skipped, 0 failed** (1773 − 56 candidate cases) |
| Real PubMedBERT NLI, `TESTING` unset, `-p nli_call_probe` | development tree, 7 files including 2 companions | 0 | 141 passed, **36 real `TextClassificationPipeline` calls**, `TESTING=None`, 4 min 25 s |
| Sentinel privacy tests | publishable tree | 0 | 7 passed |
| Base-test check | publishable vs `395c214` | — | 84 base test files and 1,356 base test functions. Apart from 4 intentionally replaced `/ingest` tests, none removed, none with fewer asserts or parameters, no new skip or xfail. The 4 asserted a stub that returned 200 with `poisoning_score: 0.0` when no ingester was configured. That route now returns 503 and reports nothing as ingested, and 3 tests cover the new behaviour and the content hash. |
| Frontend Vitest | development tree | 0 | 19 files, 155 passed; 3 Node `--localstorage-file` notices |
| `tsc -b`, production build, lint | development tree | 0 / 0 / 0 | clean; built, no warnings; 0 errors, 3 warnings present before |
| Ruff, `git diff --check` | development tree | 0 / 0 | clean |
| Gitleaks | diff and every new file | 0 | no leaks |
| `run_bandit.py` / raw Bandit | `src` (identical in both trees) | 0 / 1 | as in E3 |
| `uv lock --check --offline`, `uv sync --locked --offline --dry-run` | development tree | 0 / 0 | 162 packages; no changes |
| Integrity scripts, line-ending audit, secret-scan hook checks | publishable tree | 0 | all pass; 311 CRLF-hashed files, 0 unpinned |
| Doc tests | both | 0 | 9 passed |

- **Unchanged against `395c214`:** `trust_scoring/`, `verification/claim_verifier_v2.py`, `config/`, `data/`, `.agents/`, `.claude/`, `.githooks/`, `.gitleaks.toml` and `.bandit`. The thresholds R0–R3 are unchanged.
- **Not run:** browser scenarios on the final tree, and a real provider call in this step (the real Groq run is in section 6).

### E5. Still open

- The pending candidates: E2.
- One worker; the 5 s cleanup bound; provider-side work after a cancel; Windows-only image OCR; ASGI spec 2.4: as in D6.
- Evidence approval remains a separate human step.
