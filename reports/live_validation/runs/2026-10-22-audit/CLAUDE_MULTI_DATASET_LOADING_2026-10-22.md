# Safe multi-dataset V2 loading: implementation, audit and validation — 2026-10-22

Research tool output only. Passing tests are not clinical approval and do not make the app production-ready.

**Confirmations:**
- Claude made no commit, push, tag, merge, deployment or approval.
- `.env.local` was not modified.
- `baf6c93` and `30774eb` are unchanged.
- REL-LIVE-0003, FOOD-0001 and REL-LIVE-0004 are pending in all real project data.

## A. Implementation

**Files changed:**

| File | Change |
|---|---|
| `src/adaptive_trust_medical_rag/services/live_relationships.py` | `RelationshipRecord.dataset`; `V2_DATASETS_DIR`; `_load_v2_all`; `_load_v2(…, label)` adds provenance; an incomplete approval now reports `INCOMPLETE_APPROVAL` with its own reason (it used to read "is APPROVED, not approved") |
| `tests/e2e/test_live_multi_dataset_loading.py` (new) | 21 tests (test cases A–J below) |
| `tests/e2e/test_live_warfarin_ibuprofen.py` | `stage()` takes `fixture` and `dest`; one new mixed-dataset pipeline test |
| `scripts/build_{rel_live_0003,food_0001,rel_live_0004}_candidate.py` | `how_to_approve` text and docstrings (approval only) |
| 3 manifests in `tests/fixtures/*_candidate/` and their 3 audit-folder copies | `how_to_approve` text only; it is not covered by any hash |

**Layout:**

```
data/live_medical/relationships/
  LIVE_RELATIONSHIP_RECORDS_V1*.json         frozen V1, unchanged
  LIVE_RELATIONSHIP_RECORDS_V2*.json         optional legacy single dataset, label "v2"
  v2/<dataset>/LIVE_RELATIONSHIP_*_V2*.json  one dataset per folder, own manifest, label "v2/<dataset>"
```

**Entry point:**
- `load_relationship_store` calls `_load_v2_all`.
- `_load_v2_all` lists the legacy root dataset first if its manifest exists, then every folder under `v2/`
  in `sorted()` name order. It never relies on the operating system's directory order.
- Each dataset goes through the unchanged single-dataset `_load_v2`. No check is shared or skipped:
  - manifest `APPROVED` with both `approved_by` and `approved_at`;
  - LF-normalised SHA-256 of both files;
  - per-record checks (UNGRADED rejected);
  - per-chunk checks (content hash, provenance, https, embedding dimension, no frozen-chunk IDs);
  - `standalone_evidence_chunks`.
- Datasets are combined in memory only. No files are merged and no combined manifest is written.

**Provenance:**
- Each loaded chunk gets two keys beside its data: `dataset` (the label, which points to its manifest)
  and `dataset_approval` (`approved_by`, `approved_at`). Each record gets `dataset`.
- The hashed payload is untouched. A test checks that every original key and value of the chunk is
  unchanged.
- `source_identity`, `provenance` and `content_hash` stay as captured.

## B. Atomicity and duplicate handling

**Mechanism:**
- `_load_v2` builds each dataset into its own immutable `RelationshipStore`. It writes nothing shared.
- The wrapper collects that dataset's record IDs and chunk IDs and compares them with an `owner` map
  (ID → dataset) of the datasets already accepted.
- On any clash, the dataset is skipped **before** any of its records or chunks are added. Otherwise its
  IDs are added to `owner` and its records and chunks are appended.
- A partial load cannot happen, because nothing is published until the whole dataset is accepted.

**Diagnostics:**

| Case | Entry in `store.rejected` | Entry in `store.reason` |
|---|---|---|
| Duplicate chunk ID | `("v2/b_warfarin", "v2/b_warfarin repeats IDs already loaded from another dataset: DAILYMED-34EBEEA1-SPL-V12-SEC-5.5 (in v2/a_food)")` | `v2/b_warfarin rejected: duplicate IDs` |
| Duplicate record ID | `(…, "v2/b_spironolactone repeats IDs …: REL-LIVE-0004 (in v2/a_warfarin)")` | `v2/b_spironolactone rejected: duplicate IDs` |
| Pending, hash mismatch, incomplete approval | none | `v2/<dataset>: LIVE_RELATIONSHIP_RECORDS_V2 …` (now names the dataset) |

**Evidence:**
- Tests E, F, I and G compare the accepted records and evidence with and without the bad later dataset.
  They are equal: the later dataset left nothing behind, and the earlier dataset is intact.
- Test E's later dataset is valid on its own: one new record, one new chunk and one repeated chunk.
  Loaded alone it gives 1 record and 2 chunks; after `a_food` it contributes nothing.

## C. Builders and fixtures

| Candidate | Builder | Output folder | Fixture copy | Same bytes? |
|---|---|---|---|---|
| REL-LIVE-0003 | `scripts/build_rel_live_0003_candidate.py` | `…/2026-10-22-audit/rel_live_0003_candidate/` | `tests/fixtures/rel_live_0003_candidate/` | yes, all 3 files (`cmp`) |
| FOOD-0001 | `scripts/build_food_0001_candidate.py` | `…/food_0001_candidate/` | `tests/fixtures/food_0001_candidate/` | yes, all 3 |
| REL-LIVE-0004 | `scripts/build_rel_live_0004_candidate.py` | `…/rel_live_0004_candidate/` | `tests/fixtures/rel_live_0004_candidate/` | yes, all 3 |

- **Own folders:** each builder writes only to its own folder, as shown by the constants `OUT` and
  `REL_DIR`. No builder writes to `data/`.
- **Status:** all three are `CANDIDATE_PENDING_RESEARCHER_APPROVAL` with `approval: null`.
  REL-LIVE-0003 and REL-LIVE-0004 are `UNGRADED`. The test helper asserts both facts before every
  test-only approval.
- **Same file names:** the test with all three candidates loads three datasets that use identical file
  names, with no collision.
- **Rebuild determinism: NOT RUN.** The builders download live DailyMed and RxNav data and stamp
  `captured_at` and `retrieved_at`. A rebuild is therefore never byte-identical, and running one would
  replace the reviewed captures. Determinism is proven for loading (test J), not for building.
- **Clean checkout:** the three `tests/fixtures/*_candidate/` folders are **untracked**. A clean checkout
  lacks them, and 4 test files would fail until they are committed. Committing is your decision.

## D. Commands and results

| Command | Exit | Result |
|---|---|---|
| Earlier full run, before the audit fixes: `TESTING=1 uv run pytest -q -p no:cacheprovider -o log_cli=false tests` | 0 | 1632 passed, 0 failed, 0 errors, 120 s |
| `… pytest` on multi-dataset, warfarin, V2 evidence, provenance and audit-regression tests (`TESTING=1`) | 0 | 119 passed |
| `env -u TESTING uv run pytest … tests/e2e/test_live_warfarin_ibuprofen.py` (real PubMedBERT NLI) | 0 | 10 passed, 62 s |
| **Final full run** after all changes: same command as the first row | 0 | **1638 passed, 0 failed, 0 skipped, 0 errors**, 117 s |
| `uv run ruff check src tests` plus the 3 builders | 0 | all checks passed |
| `uv run bandit -q -r src` | 1 | 0 High, 0 Medium, 13 Low; all Low findings are in files this task did not change |
| `git diff --check` | 0 | no whitespace errors (only LF/CRLF notices) |
| `gitleaks git` and `gitleaks dir` (working diff, new test, builders, fixture files) | 0 | no leaks found |
| Secret-pattern grep of the full-suite output | 1 (no match) | 0 matches |

Frontend tests were not run: no UI contract changed. The new keys stay in the loader and init; they are
not in the candidate metadata sent to the browser.

## E. Scenario results

All results use **isolated test fixtures in pytest's `tmp_path`**, with approval and a test-only severity
set there. The actual live corpus has no V2 dataset.

| # | Scenario | Result |
|---|---|---|
| A | Legacy root dataset alone | PASSED: loads as before, labelled `v2` |
| B | One child dataset | PASSED: provenance attached; payload unchanged |
| C | FOOD-0001 + REL-LIVE-0004 | PASSED: both load, each with its own dataset |
| D | All three candidates together | PASSED: each record and chunk names its own dataset and approver; REL-LIVE-0004 → `v2/rel_live_0004` → warfarin set ID `884cdbf6…` |
| D | Init with all three | PASSED: all 3 chunks join retrieval. Each `verified_source_links` entry is that chunk's own `canonical_url`, and the two lisinopril sections sharing one label URL stay verified |
| E / I | Later dataset repeats one chunk ID among new data | PASSED: rejected whole; state equals A only |
| F | Later dataset repeats a record ID | PASSED: rejected whole, its chunk too |
| — | Root and a folder with the same IDs | PASSED: the root wins, because it is read first |
| G | Bad dataset after a good one (tampered text, wrong manifest hash, empty approval) | PASSED ×3: the good dataset is unchanged, and the diagnostic names the bad one |
| H | Pending, UNGRADED, missing `approved_by` / `approved_at` | PASSED: nothing loads |
| J | Restart (4 datasets, one rejected, loaded twice) | PASSED: equal records, evidence, status, reason and rejections |
| — | Live folder | PASSED: no `v2/` folder and no root V2 files |
| Pipeline | Warfarin + ibuprofen through the real `execute()`, with FOOD-0001 also loaded | PASSED (stand-in and real NLI): the food chunk is excluded as unrelated; the answer cites only the warfarin label (VERIFIED); the claim is SUPPORTED with identity MATCH |
| Food | FOOD-0001 reviewed wording and strength | PASSED (existing tests in `test_live_evidence_provenance.py`, `test_claim_strength.py`) |

**No new route to the model:** loaded datasets reach the model only through the existing
`supplement` → retrieval path. The identity gate, trust thresholds, claim verification, strength check
and all-or-nothing release still run on every chunk, as the pipeline test shows.

## F. Repository state at the end

- **Git:** branch `wip/pre-threads-20261022-1440`, HEAD `a96e171`. All changes are uncommitted.
  `baf6c93` and `30774eb` resolve to their original commits.
- **Live data:** `data/live_medical/relationships/` and `LIVE_MEDICAL_CORPUS_V2.json` are byte-identical
  before and after the final suite (listing and SHA-256 compared). `git status data/ .env.local` is clean.
- **Temporary files:** all test-only approvals were written under pytest's `tmp_path`, outside the
  repository. pytest keeps the last 3 runs' folders under `%TEMP%\pytest-of-sunny` (its default); the app
  never reads from there. Claude did not delete them.

## G. Remaining blockers

1. **Untracked fixtures:** the three `tests/fixtures/*_candidate/` folders are untracked, so tests fail
   on a clean checkout until they are committed.
2. **Grading and approval:** REL-LIVE-0003 and REL-LIVE-0004 need a severity grade by your documented
   method, and all three need your approval, before anything loads for real.
3. **Unattributed record rejections:** record-level entries in `store.rejected` (e.g. an UNGRADED record)
   carry the record ID but not the dataset label. An existing test asserts the exact tuple. The
   dataset-level reason names the dataset.
4. **Silent folder skip:** a `v2/<folder>` without a manifest is skipped with no diagnostic. It loads
   nothing, so it fails closed.
5. **Same text, different IDs:** the same text under two different chunk IDs in two datasets loads twice.
   Retrieval already de-duplicates by content (`live_application.py:898`).
