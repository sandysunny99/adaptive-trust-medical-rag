# Final freeze report, 2026-10-17 (evening)

This covers Sandeep's 13:00 UTC decisions. Evidence is in `followup_2026-10-17/commits2/`, `prompt_hash/` and `exact_build/`. No existing run file was overwritten. Nothing was pushed or tagged.

## Commits (local, `ui/3d-redesign`)

| Commit | Content | Staged diff |
|---|---|---|
| `2947976` | acf08ee: verified-only source links; Cloudflare 4096-token limit | 11 files (earlier) |
| `b5474ce` | provider/model trace (`served_by`) | 3 files (earlier) |
| `8d7f21e` | secret-scan hook flags for gitleaks 8.30 | 2 files, +112/-3 |
| `bf29fe8` | V2 relationship evidence loading (record stays pending) | 3 files, +422/-20 |
| `5704c33` | BLK-011: `--audit-dir`/`--run-dir`, tests in tmp dirs, 7-file guard | 2 files, +46/-2 |
| `f58e8a8` | Track A annotation package, scripts and tests, with the B110 log fix | 14 files, +3919 |
| `bafc083` | annotation prompts verified against raw bytes; CRLF pin | 3 files, +120/-4 |

- **Remote:** `git ls-remote origin refs/heads/ui/3d-redesign` still points to `c490393`.
- **Tags and index:** no tag exists, and nothing is staged.
- **How each commit was built:**
  - tracked files staged with `git apply --cached` from a reviewed patch, new files added by exact path;
  - the pre-commit secret gate passed every commit;
  - gitleaks over `c490393..bafc083` found no leaks.

**Annotation commit: what was included and left out**
- **Included:** the package source, its tests and its CLI scripts. These are what the tests import, plus source that uses the package.
- **Left out:**
  - `track_a_annotation/ai_assisted/SESSION_CONFIG_V1.json`, a generated dry-run session record. It is still untracked, in place.
  - The `__pycache__` folders, which git already ignores.
- **Already tracked:** the prompt and schema files the engine loads, so nothing more was needed.

## Prompt-hash contract

- **The frozen hashes are SHA-256 of the raw prompt bytes.**
  - `TRACK_A_LLM_FINAL_SCHEMA_HASHES_V1.json` was written by `track_a_annotation/decision_batches/gen_final_v14.py`, whose `calc_hash` opens each prompt with `"rb"`. The schema is hashed as canonical JSON.
  - All 4 recorded hashes match that method on this checkout. The adjudication prompt has 55 CRLF line endings; its CRLF bytes match and its LF form does not.
- **The fix:** the engine now hashes the raw bytes. The recorded hashes are unchanged (blob `3cbd7fad`).
- **Tests:** 8 new ones.
  - CRLF frozen as CRLF verifies, and LF frozen as LF verifies.
  - An LF copy of a CRLF-frozen prompt fails closed with "modified from frozen baseline", and so does the reverse.
  - The prompt text given to the model is unchanged.
  - The repo's real prompts match all 4 recorded hashes.
  - The recorded adjudication hash is of the CRLF bytes.
  - git pins the adjudication prompt to `eol=crlf`.
- **The pin:** `track_a_annotation/decision_batches/.gitattributes` holds the same lines as `claude/continue-blockers`: adjudication `text eol=crlf`, system and challenge `text eol=lf`.
  - The root `.gitattributes` is UTF-16, which git cannot parse.
  - Re-encoding it would activate its `-text` rule and mark `experiments/prompts/REAL_LLM_EVALUATION_PROMPT_V1_2.txt` as modified in Sandeep's working copy, so it was left alone.
- **Line-ending audit:** the audit script from `1ec75d1`, run from a scratch copy and not added to the repo, reports the adjudication prompt as **pinned**. It also lists 309 other files whose frozen hashes match only their CRLF form and are unpinned on this branch. BLK-010 is not ported, so `--check` would fail here.
- **Noted only:** `scripts/annotation/common.py` records its own text-based prompt hashes in session metadata (for example adjudication `f53f3068…`). It verifies nothing and was not changed.

## Exact-build verification of `bafc083`

The build was a fresh worktree `C:\Users\sunny\freeze-verify-bafc083`, detached at `bafc083`, with no uncommitted changes copied in. `git status` was clean before and after.

| Check | Command | Result |
|---|---|---|
| Full backend suite | `TESTING=1 pytest -q -p no:cacheprovider` | **1443 passed, 4 skipped, 0 failed** (exit 0, 337 s) |
| 7 historical files | sha256 before vs after | **identical** |
| Worktree status after suite and checks | `git status --short` | empty |
| ruff | `ruff check src/ tests/` | clean |
| Full Bandit | `.agents/scripts/ci/run_bandit.py` | exit 0 |
| Secret scan | gitleaks over `c490393..bafc083`; hook allow/deny checks | no leaks; both OK |
| Integrity | `verify_v3_1_integrity.py`, `verify_v3_confirmed_separation.py` | PASS, PASS |
| Frontend (no uncommitted frontend changes, so same code) | `vitest run`, `build`, `lint` | 15 files / **93 passed** (`--maxWorkers=2`); built; lint exit 0, same 3 warnings |
| Working copy's 7 files | sha256 vs the 2026-10-17 baseline | unchanged |
| Protected artifacts vs 2026-10-14 | `sha256sum -c` | 19 OK; app.py differs as expected (Sandeep's uncommitted NVIDIA lines plus max-tokens) |
| `data/`, `experiments/prompts`, `verification/`, `trust_scoring/`, frozen hash file | diff `c490393..HEAD` | unchanged |

Notes on these runs:
- **First vitest attempt:** it hit worker-start timeouts while the machine was under load (about 1.3 GB RAM free; another project's `vite build` was running), so 13 files never ran. The output is kept as `exact_build/vitest_attempt1_worker_start_timeout.txt`.
- **Rerun:** with two workers, all 15 files passed. That changes scheduling only, not which tests run.
- **Count difference:** the 1443 is lower than the earlier 1447 because Sandeep's uncommitted NVIDIA test additions in `tests/providers/test_vision_backend.py` are not part of `bafc083`.

## Decision table

| Field | Value |
|---|---|
| CONFIRMATION_CONTRACT_FIXED | YES |
| REAL_EMBEDDING_RETRIEVAL_VERIFIED | YES (browser runs of 2026-10-15) |
| CONTROLLED_ABSTENTION_VERIFIED | YES |
| CLOUDFLARE_OUTPUT_VALIDATED | YES (one synthetic run) |
| EVIDENCE_SOURCE_LINKS_VALIDATED | YES |
| PROVIDER_MODEL_TRACE_VERIFIED | YES for abstention and error; answer path in tests |
| RELATIONSHIP_RECORD_VERIFIED_PENDING_APPROVAL | YES (REL-LIVE-0002, review package delivered) |
| RELATIONSHIP_RECORD_APPROVED | **NO** (no approval given; records and manifests untouched) |
| EVIDENCE_BACKED_ANSWER_VERIFIED | **NO** |
| All automated checks on exact HEAD `bafc083` | **PASS** |
| APPLICATION_FREEZE_READY | **My recommendation: not yet.** Sandeep makes this call |

Why not yet, even though every check on `bafc083` passed:
1. **The live browser runs used another build.** The A/B/C/N1/N2 runs of 2026-10-15 ran on c490393 + patches + Sandeep's uncommitted NVIDIA LLM/OCR edits, not on `bafc083`. The NVIDIA edits are still uncommitted and in no commit. Either commit them and rerun the browser scenarios on that commit, or rerun the scenarios on `bafc083` as it is.
2. **BLK-010 is not ported to this branch.** 309 frozen-hash files are unpinned, so frozen-hash checks would fail on LF checkouts such as Linux CI. The Windows run above is unaffected.
3. **Still open, not resolved:**
   - B-LIVE-NVIDIA-LLM-TIMEOUT: NVIDIA's answer model timed out 4 of 4 times on 2026-10-15.
   - B-LIVE-DISCLAIMER-RESIDUE: disclaimer sentences are kept as claims, though they are withheld.
   - Neither releases unsafe content.

## Remaining working-tree state

- **Sandeep's uncommitted changes (14 files):** `.env.example`; the 7 historical run/report files; `api/app.py`, `model_registry.py` and `openai_vision_backend.py` (NVIDIA); `tests/providers/test_vision_backend.py`; both `TRACK_A_ANNOTATION_QA_V1` files.
- **Mine:** the uncommitted register edit.
- **Untracked:** `track_a_annotation/ai_assisted/`, `claude-incoming/`, the bundles and the earlier reports, unchanged.
- **Temporary worktrees, for Sandeep to remove:** `acf08ee-fullsuite-wt`, `-wt2`, `-wt3` and `freeze-verify-bafc083`.

## What Sandeep needs to do

1. Decide on the NVIDIA edits: commit them and rerun the browser scenarios on that commit, or rerun on `bafc083` without them.
2. Decide whether to port BLK-010 (the root `.gitattributes` and its 300+ pins) to this branch before any push.
3. Approve or amend REL-LIVE-0002 by naming the approver and date. Until then it stays pending and EVIDENCE_BACKED_ANSWER_VERIFIED stays NO.
4. Make the freeze call.
5. Decide when to push.
