# acf08ee revalidation and freeze assessment: 2026-10-15

Run folder: `reports/live_validation/runs/2026-10-15T0448Z-acf08ee-revalidation/`.
Machine: Sandeep's Windows PC, `C:\Users\sunny\Downloads\CASE STUDY`.
Everything below is new local evidence from this run. The cloud results quoted for reference (1353 passed / 4 skipped on c490393 + 0001 + 0002; 93 frontend tests) are not evidence for this machine.

No commit, push, branch switch, reset, clean, stash or broad restore was made. No `.env` file was opened. REL-LIVE-0001 was not approved, and nothing was written under `data/`.

## 1. Repository

- Root `C:/Users/sunny/Downloads/CASE STUDY`, branch `ui/3d-redesign`, HEAD `c490393b6d4fffc5c322e0e5274344d8c6e1cf6d` at the start and at the end.
- Status at the start: `snapshot/git_status_before.txt` (15 modified tracked files, 17 untracked entries). Diff stats, blob ids of the modified files and the worktree list are in `snapshot/`.
- Status at the end: `git_status_after.txt`. Compared with the start, these changed:
  - the 11 files of patches 0001 and 0002: 8 modified tracked files and 3 new untracked files;
  - `reports/audit/blocked_issue_register.md`, which I updated;
  - `live_application.py`, which now holds acf08ee + f97014d instead of the 16:38 edit.
- No other tracked file changed. The blob ids of all 13 other modified tracked files are unchanged, including the 7 BLK-011 files, `.env.example`, `model_registry.py`, `openai_vision_backend.py`, `test_vision_backend.py` and both TRACK_A QA files.

## 2. Patch

- **Package:** `claude-incoming/acf08ee-fix.tgz`, sha256 `3549b50f…abce` (expected). All 5 lines of `MANIFEST.sha256` are OK.
- **Patches:**
  - 0001: commit `acf08eedb73a884216fecd33059267fdb1bef3e9`, 11 files.
  - 0002: commit `f97014dfd1d8d15e15e73c590ec1be959086634d`, 3 files.
- **How they were applied:** each with `git apply --check -v`, then `git apply -v`. No `--index`, `--3way` or whitespace option was used. Logs are in `patch/`.
- **app.py:** hunk 2 applied at an offset of 19 lines, caused by Sandeep's NVIDIA LLM/OCR edits.
- **Blob check (`patch/blob_check.txt`):** 11 of the 12 files equal the "after both patches" blob.
  - `api/app.py` differs as expected. Its `--ignore-cr-at-eol` diff is Sandeep's earlier hunks plus only `CLOUDFLARE_MAX_TOKENS = 4096`, its comment line and `max_tokens=CLOUDFLARE_MAX_TOKENS` (`patch/app.py.before.diff` against `patch/app.py.after.diff`).
- **`git diff --check`:** clean.
- **Review of the diff:**
  - The `structured_output` fallback is not reintroduced.
  - The R2/R3 policy, `canonical_identity.py`, ClaimVerifierV2 and the relationship loader are untouched.
  - Only a URL listed for that exact chunk in `verified_source_links` becomes a link, and that list is empty.
  - Parse-failure and `served_by` logging carry identifiers and lengths only.
  - `served_by` takes `provider` and `model_id` from the adapter that returned the response, and `reported_model` and `finish_reason` from the provider's response body.

## 3. Backup of the rejected 16:38 change

- **Backup:** `backup/live_application.py.1638-edit`, sha256 `fe20d65c3ece195fe51963dd7b51e7b02e5157e0bb40162a7d9d82b1ecd32673`. This equalled the live file before any change, and the backup is kept.
- **Diffs:** `backup/live_application.git-diff.txt` and `backup/live_application.git-diff-ignore-cr.txt`. Apart from the `index` lines, the hunks are identical to `2026-10-14T1633Z-local-abc/live_application_midrun_change.diff`.
- **What was replaced:** `_extract_json_payload()` and a fallback that read `gen_result.structured_output`. The adapter builds `structured_output` by parsing the same response text, so the fallback cannot rescue a truncated answer.
- **How it was removed:** `git apply -R` of the saved diff (checked first). The result was byte-identical to HEAD (blob `ca88f89`).
- **To restore it:** copy the backup over the file.

## 4. Checks (outputs in `checks/`)

| Command | Exit | Result |
|---|---|---|
| `TESTING=1 pytest -q -p no:cacheprovider` on 11 focused files | 0 | **243 passed, 0 failed, 0 skipped**, 97 s. `git status` and every blob except the two patched sources were unchanged by the run. Reference: 41 failed / 163 passed with the 16:38 edit on 8 of these files |
| Full suite, temporary worktree `C:\Users\sunny\acf08ee-fullsuite-wt` (detached c490393 plus a copy of every modified tracked file and the 3 new files; blobs checked) | 0 | **1368 passed, 4 skipped**, 90 s. It rewrote the 7 BLK-011 files inside the worktree only. The worktree is left for Sandeep to remove |
| `npx vitest run` | 0 | 15 files, **93 passed**. The 4 EvidenceList source-link tests and the "not a verified link" export test ran (`vitest_sourcelink_verbose.txt`) |
| `npm run -s build` | 0 | built |
| `npm run -s lint` | 0 | 3 warnings, `react(set-state-in-effect)`, the same 3 as on 2026-10-14 |
| `ruff check src/ tests/` | 0 | All checks passed |
| `.agents/scripts/ci/run_bandit.py` | **1** | One LOW B110 (try/except/pass) at `src/adaptive_trust_medical_rag/annotation/engine.py:220`. That is Sandeep's untracked `annotation/` folder, not this patch. Bandit on the 3 patched source files: exit 0. Bandit on `src/` without that folder: exit 0 |
| `scripts/verify_v3_1_integrity.py` | 0 | PASS |
| `scripts/verify_v3_confirmed_separation.py` | 0 | PASS |
| Secret scan: gitleaks 8.30.1 `dir` on the 12 patched files, default rules and `.gitleaks.toml` | 0 | no leaks found |
| Secret scan: CI hook `pre_commit_secret_scan.py` on the 12 patched files | 1 → 0 | The hook calls `gitleaks detect … --quiet`. gitleaks 8.30.1 rejects `--quiet` (exit 126, `secret_scan_hook_gitleaks_flag_bug.txt`), and the hook reads any non-zero exit as "secrets detected", so it denies every non-test file. **This is a bug in the hook.** Its regex layer alone (CI=1) allows all 12 files |
| Protected hashes compared with `2026-10-14T1633Z-local-abc/hashes_before.sha256` | — | 19 OK, including both corpus V2 files, both relationship files, `canonical_identity.py` and `claim_verifier_v2.py`. 1 expected difference: `api/app.py` (max-tokens lines) |

## 5. Browser scenarios (kit v2, real providers, TESTING unset)

- **Backend:** `python -m uvicorn --app-dir src adaptive_trust_medical_rag.api.app:app --host 0.0.0.0 --port 8000`, started on the patched code (`backend_start.txt`).
- **Frontend:** `npm run dev` (Vite 8.3.2).
- **Ports:** both were free before the start. The process command lines are in `process_check.txt`.
- **`/health`:** 200, `"mode":"test"` reported by the app, recorded as-is.
- **Catalog:** nvidia, groq and cloudflare available; mock not available.
- **Browser and image:** Edge via the Playwright module from last time. Image `claude-incoming/abc-kit/synthetic_rx.png`, sha256 `aad8f522…2f38`.
- **Order:** the scenarios ran one at a time with `ONLY=` in the order A, B-CF, B-NV, C, N1, N2. Each json has `stream_complete: true`, and the page and the network recorded the same number of events.

| Scenario | Selection | Served by (from the stream) | embedding_mode | Retrieved / eligible / unrelated excluded | Tier / threshold / trust | Claims | Terminal |
|---|---|---|---|---|---|---|---|
| A-image | auto | groq / openai/gpt-oss-120b (reported same), finish `stop`, 1466 chars. NVIDIA tried first and timed out (backend log) | **real** (all-MiniLM-L6-v2) | 14 / 1 / 13 | R2 / 0.60 / 0.935 | 6 of 6 UNSUPPORTED, identity UNAVAILABLE | abstention |
| B-direct-cloudflare | manual, cloudflare | cloudflare / @cf/meta/llama-3.3-70b-instruct-fp8-fast (reported same), finish `stop`, 1891 chars | **real** | 14 / 1 / 13 | R2 / 0.60 / 0.935 | 8 of 8 UNSUPPORTED, identity UNAVAILABLE | abstention |
| B-direct-nvidia | manual, nvidia | `served_by: null`; `requested_model` nvidia/nemotron-3-super-120b-a12b | **real** | 14 / — / 13 | R2 / 0.60 | none generated | error LLM_ERROR "nvidia timeout" |
| C-context | auto | groq / openai/gpt-oss-120b, finish `stop`, 1435 chars (NVIDIA timed out first) | **real** | 14 / 1 / 13 | R2 / 0.60 / 0.935 | 6 of 6 UNSUPPORTED, identity UNAVAILABLE | abstention |
| N1-note-policy | auto | groq / openai/gpt-oss-120b, finish `stop`, 1635 chars (NVIDIA timed out first) | **real** | 14 / 1 / 13 | R2 / 0.60 / 0.935 | 6 of 6 UNSUPPORTED, identity UNAVAILABLE | abstention |
| N2-note-injection | auto | no model called | n/a | n/a | n/a | n/a | error INPUT_REJECTED |

What else the saved evidence shows:
- **Scenario A:**
  - Vision: `nvidia_vision` / `meta/llama-3.2-11b-vision-instruct`. It read Simvastatin and Clarithromycin, and both were confirmed.
  - `/confirm` returned 200, with medication objects as the body.
  - RxNorm: 36567 and 21212, `rxnorm_source` = `rxnorm_exact`.
  - No vision timeout this time.
- **B, C and N1:** RxNorm resolved by `cache`.
- **Risk basis everywhere:** "a multi-drug interaction question with no approved severe relationship record".
- **Eligible chunk:** the only one given to the model is `DAILYMED-SPL-SIMVASTATIN-001-CHUNK-01`. No chunk given to the model names neither drug.
- **Scenario C:** only age 58, sex male and the condition hyperlipidemia were sent. Allergies and other medicines were not sent, so they stay unknown.
- **Scenario N2:** the backend log has `additional_instructions rejected …: injection_marker (57 chars)` and the stripped-marker pattern name, but not the note text.
- **Console errors:** both error runs logged "SSE connection error" in the console when the server closed the stream after the error event.
- **Credential-shaped strings:** none in the scenario folder (`summarize_abc.py`) or in `backend.log` / `frontend.log`.
- **Files:** `scenarios/{A-image,B-direct-cloudflare,B-direct-nvidia,C-context,N1-note-policy,N2-note-injection}.{json,sse.txt,png}`, `scenarios/SUMMARY.{md,json}` and `run_abc.console.*.txt`.
  - `summarize_abc.py` wrote both summaries, then crashed while printing them to the cp1252 console (`summarize_output.txt`). The files are complete.

## 6. Cloudflare evidence

- **Provider, model and selection:** cloudflare, model `@cf/meta/llama-3.3-70b-instruct-fp8-fast`. The provider's response reported the same model. The selection was sent as `{"mode":"manual","model_id":"@cf/meta/llama-3.3-70b-instruct-fp8-fast"}`.
- **Output:** stop reason `stop`, 1891 characters. The output parsed as JSON and went through claim verification, so it was not cut off at 256 tokens.
- **Parse-failure path:** it was not triggered live, so its message and log line are covered only by tests (`test_answer_cut_off_at_the_token_limit_says_so_and_logs_no_content` and `test_answer_that_is_not_json_keeps_the_plain_parse_message`).
- **Logging:** no generated content is logged. INFO lines from the app loggers do not print under plain uvicorn, so the `LLM output received` line is not in `backend.log`. `served_by` in the stream carries only identifiers, the stop reason and the length.

## 7. Evidence-source links

- **Tests:**
  - backend: `tests/e2e/test_live_source_links.py`, plus 2 tests in `test_live_failure_semantics.py`, all passed;
  - frontend: 4 EvidenceList tests and 1 export test, all passed.
- **Corpus statuses (tested):** 11 PLACEHOLDER, 2 SHARED, 1 UNVERIFIED, 0 VERIFIED.
- **Live:** every evidence item had `source_link_status: PLACEHOLDER` and no `url`. The B-CF screenshot shows the placeholder URL as text, followed by "Not linked: Placeholder link in the frozen corpus; it does not identify the original document."
- **Still not verified:** all 14 corpus sources. No source record is approved.

## 8. Relationship V2 evidence review (not approved)

- **Capture re-verified (`source_review/capture_reverify.txt`):** all 6 captured files match the sizes and sha256 values in the manifest.
  - Clarithromycin SPL setid `9aaffb41-408c-4372-8fd5-1d649450c0e9`, version 21, effectiveTime 20231010.
  - Bytes 75723–76181 are exactly one `<paragraph>` under the heading "4.5 Lomitapide, Lovastatin, and Simvastatin", raw sha256 `1bc9541f…e874`. It contains inline markup and a non-breaking space.
  - RxNav: 36567 is simvastatin and 21212 is clarithromycin, both TTY IN and not suppressed.
- **Candidate files:** `relationship_v2_candidate/` (builder: `source_review/build_v2_candidate.py`).
  - `LIVE_EVIDENCE_SUPPLEMENT_V2_CANDIDATE.json`: one chunk `DAILYMED-SPL-9aaffb41-408c-4372-8fd5-1d649450c0e9-V21-S4.5-P1`. Its text has tags removed, entities unescaped and whitespace collapsed. Content sha256 `056d8009…`. It carries a 384-dimension all-MiniLM-L6-v2 embedding (same call as `build_live_corpus_v2.py`) and the full byte-offset provenance.
  - `LIVE_RELATIONSHIP_RECORDS_V2_CANDIDATE.json`: REL-LIVE-0002, simvastatin 36567 → clarithromycin 21212, CONTRAINDICATION, CONTRAINDICATED, BIDIRECTIONAL. The evidence span is the chunk text.
  - The manifest: status `CANDIDATE_PENDING_RESEARCHER_APPROVAL`, `approval: null`, records sha256 `aefc2c83…` (LF-normalised). No reviewer or approval time is filled in.
- **Validation:** `validate_record` returns "valid" against the supplement chunk. Against the frozen corpus alone it returns "source chunk … is not in the live corpus". So the production loader cannot use this candidate even after approval, without a separate reviewed decision on how the supplement enters retrieval. The frozen corpus is not changed.

## 9. Register changes (`reports/audit/blocked_issue_register.md`)

| Row | New status | Evidence |
|---|---|---|
| B-WORKING-COPY-MIDRUN-EDIT (added) | CLOSED | Backup retained; focused tests 243/0 |
| B-LIVE-CLOUDFLARE-OUTPUT (added) | CLOSED (one synthetic live run) | max_tokens 4096; tests; B-CF parsed with finish `stop` |
| B-EVIDENCE-SOURCE-LINKS (added) | Implementation CLOSED; verified-source approval OPEN | Tests, live evidence items and screenshot |
| B-LIVE-PROVIDER-TRACE (added) | Verified for the abstention and error paths; answer path test-only | `served_by` in every saved terminal event; auto runs name the failover provider |
| B-LIVE-DISCLAIMER-RESIDUE (added) | OPEN | Disclaimer sentences in claim 0 of A, B-CF, C and N1 while `removed_disclaimers` is `[]` (those claims are withheld) |
| B-LIVE-NVIDIA-LLM-TIMEOUT (added) | OPEN | NVIDIA answer model timed out 4 of 4 times |
| B-LIVE-EXTRACTION | LIVE_VERIFIED; reliability record added | The 2026-10-14 timeout and retry kept; first-attempt success today |
| B-REDESIGN-CONFIRM | LIVE_VERIFIED (local) | Objects sent, `/confirm` 200, terminal reached |
| B-LIVE-RISK-ELIGIBILITY | LOCAL RUN VERIFIED (R2); R3 awaiting an approved record | Saved retrieval events with `embedding_mode: real`, counts and basis |
| B-CLAIM-EVIDENCE | BLOCKED_RESEARCHER_DECISION (unchanged); V2 candidate pending | Section 8 |
| B-LIVE-E2E-SECURITY | BLOCKED_RESEARCHER_DECISION (unchanged); N1 and N2 evidence added | Section 5 |
| BLK-011 | NOT FIXED ON ui/3d-redesign | Full suite in the worktree rewrote all 7 files |

Human relevance, claim-evidence benchmark, Free Replication V1 and Cognee are unchanged.

## 10. Decision table

| Field | Value | Basis |
|---|---|---|
| CONFIRMATION_CONTRACT_FIXED | YES | A: objects sent, `/confirm` 200, terminal reached |
| REAL_EMBEDDING_RETRIEVAL_VERIFIED | YES | Saved `retrieval` events with `embedding_mode: "real"` for A, B-CF, B-NV, C and N1 |
| CONTROLLED_ABSTENTION_VERIFIED | YES | A, B-CF, C and N1 abstained with every claim withheld; N2 rejected at input |
| RELATIONSHIP_RECORD_VERIFIED_PENDING_APPROVAL | YES (V2 candidate, run folder only) | Byte-exact capture re-verified; candidate validates against its own chunk; activation path undecided |
| RELATIONSHIP_RECORD_APPROVED | NO | Nothing approved |
| EVIDENCE_BACKED_ANSWER_VERIFIED | NO | No approved record; no released answer |
| CLOUDFLARE_OUTPUT_VALIDATED | YES (one synthetic run) | B-CF parsed, finish `stop` |
| EVIDENCE_SOURCE_LINKS_VALIDATED | YES (behaviour) | No unverified URL is linked; no source verified |
| PROVIDER_MODEL_TRACE_VERIFIED | YES for abstention and error; answer path test-only | Section 5 |
| APPLICATION_FREEZE_READY | **NO** | Conditions 1 and 9 below |

Safe-abstention-only conditions:

| # | Condition | Met? | Why |
|---|---|---|---|
| 1 | The tested build is a recorded revision | **Not as a revision** | The code is an uncommitted working copy: c490393 + patches + Sandeep's edits, recorded by blob ids in `hashes_after.sha256` |
| 2 | 16:38 conflict resolved, focused tests pass | Yes | |
| 3 | A/B/C streams retained | Yes | |
| 4 | `embedding_mode: "real"` on every applicable run | Yes | |
| 5 | Tier, basis and unrelated-evidence filtering traceable | Yes | |
| 6 | Unsupported claims withheld; N1 and N2 effective | Yes | |
| 7 | Provider and model recorded | Yes | |
| 8 | No unverified URL presented as a link | Yes | |
| 9 | Regression, security and integrity checks pass | **Not all as written** | `run_bandit.py` exits 1 on a LOW finding in the untracked `annotation/engine.py`; the CI secret-scan hook is broken by the gitleaks `--quiet` flag (the direct gitleaks scan is clean); BLK-011 still rewrites evidence on a full run |
| 10 | Frozen corpus and protected artifacts unchanged | Yes | |

## 11. What Sandeep needs to do

1. **Freeze revision.** Decide whether to commit the patched working copy (patches + NVIDIA edits) as the freeze revision. I have not committed.
2. **Bandit failure.** Decide how to clear the LOW B110 in the untracked `src/adaptive_trust_medical_rag/annotation/engine.py:220`: fix it, add a `# nosec` with a reason, or keep the folder out of the freeze. `run_bandit.py` fails on any severity.
3. **Secret-scan hook.** Approve a one-line fix to `.agents/scripts/{,ci/}pre_commit_secret_scan.py`: drop `--quiet` or use `--no-banner`.
4. **BLK-011.** Decide whether to bring the BLK-011 isolation fix onto `ui/3d-redesign`.
5. **NVIDIA timeouts.** NVIDIA answer calls time out at 30 s. Decide whether NVIDIA stays first in automatic order and whether B-NV should be rerun.
6. **V2 candidate.** Review `relationship_v2_candidate/`, then approve, amend or reject it. Also decide how a supplementary evidence chunk may enter retrieval without changing the frozen corpus. REL-LIVE-0001 stays unapproved.
7. **Worktree.** Remove the temporary worktree when done: `git worktree remove C:\Users\sunny\acf08ee-fullsuite-wt`.

Still running: the backend on :8000 and Vite on :5173, both serving the patched code and logging into this folder.
