# Follow-up 2026-10-17: two local commits, Bandit B110, BLK-011, REL-LIVE-0002 review package

This addendum covers Sandeep's 2026-10-17 06:51 UTC instructions. Evidence is in `followup_2026-10-17/`, and the review package is in `relationship_v2_candidate/REVIEW_PACKAGE/`. No existing run file was overwritten.

## Commits (local only)

| Commit | Content | Staged |
|---|---|---|
| `8d7f21e` | fix(ci): run the secret-scan hook's gitleaks step with flags gitleaks 8.30 accepts | `.agents/scripts/ci/pre_commit_secret_scan.py` (+16/-3) via `git apply --cached`; new `tests/test_ci_secret_scan_gitleaks.py` (+96). 2 files, +112/-3 |
| `bf29fe8` | feat(live): load approved V2 relationship records with their own versioned evidence | `services/live_relationships.py` (+118/-2) and `services/live_application.py` (+25/-18, only the V2 changes) via `git apply --cached`; new `tests/e2e/test_live_relationship_evidence_v2.py` (+279, 35 tests). 3 files, +422/-20 |

- **History:** `bf29fe8` ← `8d7f21e` ← `b5474ce` ← `2947976` ← `c490393`.
- **No push or tag:** `git ls-remote origin refs/heads/ui/3d-redesign` and `origin/ui/3d-redesign` both point to `c490393`, and `git tag --points-at HEAD` is empty.
- **Staging:** no `git add -A`, `.`, `-a` or `--no-verify` was used, and the pre-commit secret gate passed both commits.
- **Records and diffs:** staged diffs and commit messages are in `followup_2026-10-17/commits/`.

## B. Hook fix (`followup_2026-10-17/hook/`)

- **Flags:** `--quiet`, which gitleaks 8.30.1 rejects, is replaced by `--no-banner --log-level error --redact --exit-code 1`.
- **Exit codes:** exit 1 means a secret was found. Any other non-zero exit means "GITLEAKS COULD NOT RUN" and still blocks.
- **Heading fix during this follow-up:** the deny reason started with "SECRET DETECTED" even when the scan had only failed to run. It now starts with "SECRET SCAN COULD NOT RUN" in that case (`hook_checks_attempt1_misleading_heading.txt` shows the earlier output).
- **Tests:**
  - 10 hook and scanner tests pass. They cover the command line, exit 1 blocks, exit 2/126/-1 block as "could not run", the heading for each case, and clean content allowed.
  - Real gitleaks: a random fake GitHub-token-shaped string, generated in memory, is denied by both the gitleaks and regex layers. Clean code and env-var references are allowed.
  - `check_secret_scan_allow.py` and `check_secret_scan_deny.py` pass locally and with CI=1.
  - With a fake `gitleaks.bat` that exits 126 first on PATH, the real hook denies with "SECRET SCAN COULD NOT RUN".
- **Coverage not weakened:** the same fake token gives exit 1 with both the old flag set (minus `--quiet`) and the new one.
- **Commit gate** (`commit_gate_demo.txt`): in a throwaway repo with `.githooks`, `.gitleaks.toml` and the scanner, a staged fake token blocked the commit (regex finding and gitleaks `github-pat`, secret redacted), and a clean commit succeeded. The repo was deleted afterwards.
- **Pre-existing behaviour, noted:** the hook's `except Exception: return []` (for example a gitleaks timeout) still allows the write. It is unchanged.

## C. V2 loader (`bf29fe8`)

- **Behaviour:** as described in `ADDENDUM_DECISION_B_AND_V2_PATH.md` section 3.
- **Untouched (checked against HEAD before committing):** `canonical_identity.py`, `claim_verifier_v2.py`, `trust_scoring/` and `data/`. `TRUST_THRESHOLDS` is still R0 0.30 / R1 0.45 / R2 0.60 / R3 0.75.
- **Tests before the commit:** 235 passed. That is the 35 V2 tests plus risk/eligibility, failure semantics, additional instructions, source links, image confirmation, canonical identity, claim verifier and the confirmation contract (`followup_2026-10-17/checks/v2_pre_commit_checks.txt`).

## D. Bandit B110 (uncommitted; Sandeep's untracked file)

- **The change:** in `src/adaptive_trust_medical_rag/annotation/engine.py`, the fallback adapter `except Exception:` now binds `exc` and calls the module's existing `logger.warning`. The log line holds the provider and `type(exc).__name__` only, never `str(exc)`. The except clause is just as broad, and the method still returns None, so `annotate_position` still raises "not configured or missing credentials".
- **Hashes:** sha256 before `3ed51a99…de80`, after `671b19c1…f886`. The backup is `followup_2026-10-17/engine_b110/engine.py.before`.
- **New test (uncommitted):** `tests/test_annotation_engine_backend_init.py`, 5 tests, all passing:
  - HuggingFace and FreeLLMAPI initialize their adapter;
  - a failed init logs WARNING with the provider and "RuntimeError" and leaves out the message;
  - annotation without a backend still fails safely;
  - an unknown provider logs nothing.
- **Bandit and ruff:** Bandit on `engine.py` exits 0, `run_bandit.py` over all of `src/` exits 0, and ruff is clean.
- **Pre-existing failures, not caused by this change:** 3 tests in Sandeep's `tests/annotation/test_annotation_schemas.py` fail with PromptHashMismatchError. The original `engine.py` fails identically (`engine_b110/preexisting_prompt_hash_failure.txt`). The frozen hash is of the prompt's CRLF bytes, and `_load_text` reads in text mode. New register row: B-ANNOTATION-PROMPT-HASH-EOL.

## E. BLK-011 (uncommitted port)

- **Source:** commit `e41cae2` "fix(cli): stop test and simulation runs overwriting committed run evidence". It is not on origin. It is in the untracked `continue-blockers.bundle`, which I verified and fetched into FETCH_HEAD only (no branch, no checkout).
- **How it was ported:** `cli.py` and `tests/test_cli.py` at HEAD equal `e41cae2`'s parent, so its diff was applied to the working tree with `git apply`, without touching the index.
- **What it adds:** `--audit-dir` and `--run-dir` (defaults unchanged); the two `research-run` tests use tmp dirs; a regression test fails if a run changes the protected files. I widened that test from 4 to all 7 files.
- **Writers:** all 7 writes are in `handle_research_run`, and every `research-run` test now passes the temp folders.
- **Isolated full suite:** `C:\Users\sunny\acf08ee-fullsuite-wt3`, detached `bf29fe8` plus every uncommitted working-copy change (blob-identical; `blk011/isolated_copy_contents.txt`). Result: **1447 passed, 4 skipped, 3 failed**, the 3 being the pre-existing prompt-hash tests above.
  - The SHA-256 of the 7 files before and after are identical (`blk011/seven_before.sha256` = `seven_after.sha256`).
  - `git status` was unchanged.
  - Nothing was restored after the run.
- **Working copy:** `tests/test_cli.py` passed 20, and the working copy's 7 files were unchanged.

## F. Verification of the final state (HEAD `bf29fe8` plus the uncommitted working copy)

| Check | Result |
|---|---|
| Full backend suite (isolated copy wt3) | 1447 passed, 4 skipped, 3 failed (pre-existing B-ANNOTATION-PROMPT-HASH-EOL) |
| Hook tests | 10 passed |
| V2 and live-pipeline set before the V2 commit | 235 passed |
| B110 tests | 5 passed |
| test_cli (working copy) | 20 passed, 7 files unchanged |
| vitest / build / lint | 93 passed / built / exit 0 with the same 3 warnings |
| ruff `src/ tests/` | clean |
| `run_bandit.py` (full `src/`) | **exit 0** |
| gitleaks over the 4 local commits (`c490393..HEAD`) | no leaks |
| gitleaks and the CI hook over the uncommitted changed files | no leaks; 4 of 4 allowed |
| verify_v3_1_integrity / verify_v3_confirmed_separation | PASS / PASS |
| Protected hashes vs 2026-10-14 | 19 OK; app.py differs as expected (max-tokens) |
| `data/`, `experiments/prompts`, `verification/`, `trust_scoring/` | unchanged |

## G. REL-LIVE-0002 review package

`relationship_v2_candidate/REVIEW_PACKAGE/` holds:
- exact copies of the r1 and r2 files, and text versions with the embedding abbreviated (384 floats, sha256 `0bcb0ce1…d1f5`);
- the capture manifest, the recomputed hashes, the raw byte range and the RxNav responses;
- the 34-check report, rerun today (34/34);
- the loader diff and the list of the 35 test names.

The candidate files are byte-identical before and after packaging. No approved copy was loaded into the application today. Both records stay CANDIDATE_PENDING_RESEARCHER_APPROVAL with approval null.

## Freeze decision

| Field | Value |
|---|---|
| APPLICATION_FREEZE_READY | **NO** |
| EVIDENCE_BACKED_ANSWER_VERIFIED | **NO** |
| RELATIONSHIP_RECORD_APPROVED | NO |

What still blocks the freeze:
1. **The tested build is not one commit:** `bf29fe8` plus uncommitted changes. Those are Sandeep's NVIDIA LLM/OCR edits, the BLK-011 port, the B110 fix and the two new test files.
2. **The full suite is not green:** 3 failures from B-ANNOTATION-PROMPT-HASH-EOL in the untracked annotation tests.
3. **Still open:** B-LIVE-DISCLAIMER-RESIDUE and B-LIVE-NVIDIA-LLM-TIMEOUT.

The evidence-backed answer additionally needs Sandeep's approval of REL-LIVE-0002 and a real end-to-end positive run with negative controls.

## What Sandeep needs to do

1. Review `relationship_v2_candidate/REVIEW_PACKAGE/`, then approve, amend or reject REL-LIVE-0002.
2. Decide on a third commit for the BLK-011 port (`cli.py`, `tests/test_cli.py`).
3. Commit (or not) the B110 fix and its test with the annotation work.
4. Choose a fix for B-ANNOTATION-PROMPT-HASH-EOL.
5. Decide whether to commit the NVIDIA edits, so one commit equals the tested build.
6. Remove the temporary worktrees `C:\Users\sunny\acf08ee-fullsuite-wt`, `-wt2` and `-wt3` when done.
