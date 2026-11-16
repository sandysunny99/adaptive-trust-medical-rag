# Multi-dataset loader: final hardening and clean-checkout check — 2026-10-22

Research tool output only. Passing tests are not clinical approval and do not make the app production-ready.
This report follows `CLAUDE_MULTI_DATASET_LOADING_2026-10-22.md`.

**Confirmations:**

- Claude made no commit, push, tag, merge, deployment or approval.
- `.env.local` was not modified.
- `baf6c93` and `30774eb` are unchanged.
- REL-LIVE-0003, FOOD-0001 and REL-LIVE-0004 are pending in all real data, and both relationship
  candidates are still UNGRADED.

## 1. Fixes made

**`src/adaptive_trust_medical_rag/services/live_relationships.py`:**

| Change | Before | After |
|---|---|---|
| Missing manifest | A `v2/<folder>` without `LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json` was skipped silently. With only such folders, the V2 result was dropped entirely. | Rejection `("v2/<folder>", "v2/<folder> has no LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json, so nothing in it was loaded")`, the same text in `reason`, and a warning log. No approval or hash error is emitted for it. |
| Record and chunk rejection attribution | `("REL-LIVE-0004", "severity UNGRADED is not one of […]")` | `("REL-LIVE-0004", "v2/rel_live_0004: severity UNGRADED is not one of […]")`. The tuple shape and record ID are kept; the reason is prefixed with the dataset. |
| Per-record log lines | named the file | name the dataset label |

No validation rule changed.

**Who reads `store.rejected`:** no code in `src/` reads it. Of the tests:

- three match by substring and still pass unchanged;
- one matches an exact tuple and was updated (`tests/e2e/test_live_evidence_provenance.py:242`, now
  `"v2: severity UNGRADED …"`).
- V1 rejections (`("V1", …)`) are unchanged.

## 2. Identical text from different sources

**Code path:** in `services/live_application.py:874-902`, every retrieved chunk passes the medication
alignment check, then the source-identity gate, then content de-duplication.

- **Dedup:** the first verified copy in retrieval order is kept. Later copies with the same text are
  dropped before scoring, so they never reach eligibility, the prompt, citations or `excluded_sources`.
- **Relationship identity:** `RelationshipStore.identity_for_chunk` gives an identity only from a record
  that names **that exact chunk ID and content hash**. A record can never lend its support to another copy.

**Fixture:** dataset A is REL-LIVE-0004. Dataset B has the same text under chunk ID
`TEST-SYNTHETIC-B-SEC-7.3` with a **synthetic, test-only** DailyMed set ID (`0000000b-…`). Both pass
`check_source_identity`, so both are verified.

Tests in `tests/e2e/test_live_warfarin_ibuprofen.py`:

| Scenario | Outcome | Source used and cited | Other copy (dropped by de-duplication) |
|---|---|---|---|
| A ranked first, B has its own record | answer; claim SUPPORTED / MATCH | A's label only | B's URL appears **nowhere in the whole SSE stream** |
| B ranked first, B has its own record | answer | B's URL only | A's URL nowhere in the stream |
| B ranked first, B has **no** record | **abstains** (identity UNAVAILABLE) | no answer is released; A's record is not lent to B | A's URL not in the result |

Across scenarios:

- **Two fresh loads:** same kind, evidence URLs and support states.
- **In every case:** both copies keep their own `content_hash`, `source_identity` and `dataset`;
  `dataset_approval` never appears in the SSE stream (provenance stays internal).

**Verdict:** the current behaviour is safe, so no code change was made to retrieval.

**Side effect (safe, not fixed):** when a copy without a record outranks the copy that has one, the
pipeline abstains even though supported evidence exists.

## 3. Isolation and atomicity matrix

All cases run on temporary copies under pytest's temp folder. Approval and test-only grading exist only
there.

| # | Case | Test | Result |
|---|---|---|---|
| A | Legacy root only | `test_a_root_level_dataset_alone_loads_as_before` | PASSED |
| B | One child dataset; hashed payload unchanged | `test_one_approved_dataset_loads_with_its_provenance` | PASSED |
| C | FOOD-0001 + REL-LIVE-0004 | `test_food_and_a_relationship_dataset_load_together_with_their_provenance` | PASSED |
| D | All three candidates; init; own source link each | `test_all_three_candidates_coexist_with_their_own_provenance`, `test_all_datasets_reach_retrieval_and_each_links_to_its_own_source` | PASSED |
| E | Later dataset repeats a chunk ID (mostly new data) | `test_a_later_dataset_repeating_a_chunk_id_is_rejected_whole` | PASSED: state equals the earlier datasets alone |
| F | Later dataset repeats a record ID | `test_a_later_dataset_repeating_a_record_id_is_rejected_whole` | PASSED: state equal |
| G | Tampered text, wrong manifest hash, empty approval after a good dataset | `test_a_bad_dataset_does_not_affect_a_good_one` ×3 | PASSED: state equal |
| H | Missing manifest (empty folder; data files only) after a good dataset; a lone empty folder | `test_a_folder_without_a_manifest_is_reported_and_loads_nothing` ×2, `test_only_a_folder_without_a_manifest_still_reports_it` | PASSED: state equal; reason names the folder |
| I | UNGRADED in two datasets, plus a bad-hash record in a third | `test_record_rejections_in_two_datasets_name_each_dataset` | PASSED: each rejection names its dataset |
| J | Identical text from two verified sources | section 2 (4 tests) | PASSED |
| K | Restart and stable order | `test_loading_is_deterministic_across_restarts`, `test_the_same_text_result_is_the_same_after_a_restart` | PASSED |
| — | Root takes precedence over a folder | `test_the_root_dataset_takes_precedence_over_a_folder_with_the_same_ids` | PASSED |
| — | Pending / UNGRADED / incomplete approval | 4 tests: `test_a_pending_dataset_loads_nothing`, `test_an_ungraded_relationship_dataset_is_rejected`, `test_incomplete_approval_metadata_is_rejected` ×2 | PASSED |

"State equal" means the accepted records and evidence after loading the bad dataset equal those loaded
without it.

## 4. Clean-checkout requirements

**Files a future commit must include.** These 15 untracked files are needed, beyond the 28 modified
tracked files:

```text
src/adaptive_trust_medical_rag/services/claim_strength.py      <- imported by live_application.py; without it the app does not start
tests/test_claim_strength.py
tests/e2e/test_live_multi_dataset_loading.py
tests/e2e/test_live_warfarin_ibuprofen.py
tests/fixtures/food_0001_candidate/LIVE_RELATIONSHIP_EVIDENCE_V2.json
tests/fixtures/food_0001_candidate/LIVE_RELATIONSHIP_RECORDS_V2.json
tests/fixtures/food_0001_candidate/LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json
tests/fixtures/rel_live_0003_candidate/LIVE_RELATIONSHIP_EVIDENCE_V2.json
tests/fixtures/rel_live_0003_candidate/LIVE_RELATIONSHIP_RECORDS_V2.json
tests/fixtures/rel_live_0003_candidate/LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json
tests/fixtures/rel_live_0004_candidate/LIVE_RELATIONSHIP_EVIDENCE_V2.json
tests/fixtures/rel_live_0004_candidate/LIVE_RELATIONSHIP_RECORDS_V2.json
tests/fixtures/rel_live_0004_candidate/LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json
scripts/build_food_0001_candidate.py
scripts/build_rel_live_0004_candidate.py
```

**Tests that read the fixtures:**

- `test_live_evidence_provenance.py`
- `test_live_audit_regressions.py`
- `test_live_warfarin_ibuprofen.py`
- `test_live_multi_dataset_loading.py`

**Fixture review:**

- Each folder holds exactly the 3 V2 files.
- Each is byte-identical (`cmp`) to its copy in `reports/…/2026-10-22-audit/`.
- The content is DailyMed label text, provenance, identity record and embedding.
- The status is pending with `approval: null`, prepared by "Claude (AI-prepared candidate; not a reviewer)".
- The scan for email, SSN, phone, MRN and DOB patterns found nothing, and gitleaks found no leaks.

**Clean-checkout simulation:**

- **Setup:** a detached worktree at `HEAD` (`C:\Users\sunny\cwt-mds`), the tracked diff applied
  (`git diff HEAD --binary`), and the 15 files above copied in.
- **Environment:** `uv sync --frozen --offline`.
- **Command:** `TESTING=1 uv run pytest -q -p no:cacheprovider -o log_cli=false tests`.
- **Result:** exit 0, **1642 passed, 4 skipped, 0 failed**.
- **The 4 skips** are `test_provider_connectivity_preflight.py` (GROQ, GEMINI, HF, Cloudflare keys not
  set). They are expected, because a checkout never contains `.env.local`.
- **Afterwards** the worktree was removed with `git worktree remove --force`, followed by
  `git worktree prune`. The other, pre-existing worktrees are untouched.

**Limitation:** this simulates the commit; it is not a checkout of a real commit. It proves the suite
passes when exactly those files are tracked.

## 5. Commands and results (after the final change)

| Command | Exit | Result |
|---|---|---|
| `TESTING=1 uv run pytest -q -p no:cacheprovider -o log_cli=false --basetemp=<scratchpad> -rs tests` (main checkout) | 0 | **1646 passed, 0 skipped, 0 failed, 0 errors**, 167 s |
| `env -u TESTING uv run pytest … tests/e2e/test_live_warfarin_ibuprofen.py` (real PubMedBERT NLI) | 0 | 14 passed |
| Clean-worktree full suite (section 4) | 0 | 1642 passed, 4 skipped (no credentials) |
| `uv run ruff check src tests` plus the 3 builders | 0 | all checks passed |
| `uv run bandit -q -r src` | 1 | Low 13, Medium 0, High 0 (unchanged; all in files not touched by this task) |
| `git diff --check` | 0 | no whitespace errors |
| `gitleaks dir` on one scan folder holding the tracked working diff (`git diff`), the 15 untracked files and `CLAUDE_MULTI_DATASET_LOADING_2026-10-22.md` (this report did not exist yet) | 0 | no leaks found |
| Later, separate scan after the layout edits: `gitleaks dir` on this report only | 0 | no leaks found |
| Secret-pattern grep of the suite output | — | 0 matches |
| `cd frontend && npx vitest run` (run afterwards, no code change in between) | 0 | 19 files, 126 passed (two full runs). A first run filtered through grep and head showed "6 files, 21 tests"; the cause is unconfirmed (probably an interim summary). |
| `cd frontend && npx tsc --noEmit -p .` | 0 | no type errors |

1646 on the main checkout equals 1642 + 4 in the worktree: the same tests, with credentials present.
No API or SSE field changed, and the new test asserts that `dataset_approval` is absent from the stream.

**Live HTTP/SSE/browser validation of combined datasets:** deferred by your decision until candidates are
graded and approved, then run once against the real activation.

**Commit review:** `experiments/runs/live-smoke-v1/{case_results.jsonl, manifest.json, summary.json}`
were modified before this session and are run output, not code. Whether they belong in the commit is
your decision.

## 6. Final state

- **Git:** branch `wip/pre-threads-20261022-1440`, HEAD `a96e171`; 28 modified tracked files and the 15
  untracked files above. Nothing committed.
- **Live data:** `data/live_medical/relationships/` holds only the V1 files and `source_capture`. Its
  listing and the SHA-256 of all its JSON files and `LIVE_MEDICAL_CORPUS_V2.json` match the baseline
  taken before this task. `git status data/ .env.local` is clean.
- **Temporary files:**
  - pytest folders `pytest-481`–`483` (this pass's targeted runs, 20:06–20:07, no pytest running) were
    deleted, so `%TEMP%\pytest-of-sunny` is empty;
  - the scratchpad `--basetemp` and scan-copy folders were deleted;
  - no approved V2 copy remains anywhere.

## 7. Remaining issues

**Completed in this pass:**

- missing-manifest diagnostic;
- dataset attribution of record rejections;
- citation safety for identical text, proven by a test;
- the H–K matrix;
- clean-checkout simulation;
- final full run.

**Still open:**

1. **Commit:** the 15 files in section 4 must be part of the eventual commit (your decision); otherwise a
   checkout lacks `claim_strength.py` and the fixtures.
2. **Abstention from dedup order:** when a copy without a record outranks the copy that has one, the
   pipeline abstains (section 2). This is safe; improving it would mean preferring the record-bearing
   copy, which is new logic not requested here.
3. **Candidate governance:** FOOD-0001's reviewed wording needs your review. REL-LIVE-0003 and
   REL-LIVE-0004 need a severity grade by your documented method. All three need your explicit approval.
4. **No live run:** no HTTP, SSE or browser run was made for this pass (loader and pipeline tests only).
