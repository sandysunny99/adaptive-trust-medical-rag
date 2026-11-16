# Leftover files review (read-only), 2026-10-19

This review covers Sandeep's 06:44 UTC request. Nothing was deleted, moved, staged, committed or pushed.
- `git status`, HEAD (`30774eb`) and `git worktree list` were identical before and after the review.
- GitHub `ui/3d-redesign` = `30774eb`.
- No env file was opened, and no file in `claude-incoming/` was opened (names, sizes and hashes only).

## Summary

| # | Item | Size | Git status | Recommendation | Reason |
|---|---|---|---|---|---|
| 1 | Worktree `C:\Users\sunny\acf08ee-fullsuite-wt` (base `c490393`) | 87 MB | separate worktree, 25 uncommitted entries | **Safe to remove** (`git worktree remove --force`) | No unique code: every code file's content is already a blob in the repo, all but two equal current HEAD. The only unique files are the 7 historical files as the full suite rewrote them (simulation output, regenerable) |
| 1 | Worktree `acf08ee-fullsuite-wt2` (base `b5474ce`) | 87 MB | 19 uncommitted entries | **Safe to remove** (`--force`) | Same as above, plus an intermediate copy of the blocker register that the committed register supersedes |
| 1 | Worktree `acf08ee-fullsuite-wt3` (base `bf29fe8`) | 87 MB | 22 uncommitted entries | **Safe to remove** (`--force`) | Same; its 7 historical files equal Sandeep's working copy; the annotation folders it holds are now committed (`f58e8a8`) |
| 2 | `redesign-upload-fix.bundle` (2026-10-13) | 12 KB | untracked | **Safe to remove** | Head `7dbce26` (`claude/redesign-upload-fix`) is already on `origin/main` and `origin/ui/3d-redesign` |
| 2 | `continue-blockers.bundle` (2026-10-13) | 820 KB | untracked | **Keep** | Head `1ec75d1` (`claude/continue-blockers`) is on no local or remote branch; the bundle is the only durable copy (source of the BLK-010/BLK-011 ports; `e41cae2` exists locally only as an object fetched from it; `d834830` is not found anywhere) |
| 2 | `redesign-fixes.bundle` (2026-10-14) | 12 KB | untracked | **Keep / Needs Sandeep** | Head `c11a7ee` (`claude/redesign-fixes`) is not in the local repository; the local branch `claude/redesign-fixes` is at `988203a`. The bundle holds a commit found nowhere else |
| 3 | `claude-incoming/abc-kit/` (5 files, 2026-10-14: `KIT_README.md`, `run_abc.mjs`, `run_abc_api.py`, `summarize_abc.py`, `synthetic_rx.png`) | ~48 KB | untracked | **Keep** | `docs/TESTING.md` names this folder as the browser-kit location; `synthetic_rx.png` (sha256 `aad8f522…`) is the scenario-A test image |
| 3 | `claude-incoming/acf08ee-fix/` and `acf08ee-fix.tgz` (2026-10-15) | ~101 KB | untracked | **Needs Sandeep** (could be removed) | The two patches were applied as commits `2947976` and `b5474ce`. Kit v2 (`abc-kit-v2/`) was used for every browser run since 2026-10-15; keep it if the browser scenarios will be rerun |
| 4 | `cognee_service/` (`model_cache/huggingface/…PubMedBERT-MNLI-MedNLI`, 2026-10-08) | 419 MB | untracked, weights file git-ignored | **Keep** | The only content is the pinned NLI model cache, read by `tests/test_claim_verifier_v2.py`, `tests/test_claim_verifier_v2_t23.py` and many `experiments/*.py`. It could be re-downloaded, but the tests and experiments expect this path |
| 5 | `.cursor/` | 0 bytes (empty) | untracked | **Safe to remove** | Empty editor folder; nothing references it |
| 5 | `.playwright-mcp/` (screenshots from 2026-10-13, `after/01-overview.png` …) | 17 MB | git-ignored | **Needs Sandeep** | UI review screenshots from the redesign; regenerable only by repeating that review |
| 5 | `scratch/` (research helper scripts and JSON, 2026-09-07 to 2026-10-18) | 4.9 MB | git-ignored | **Needs Sandeep** | Researcher's own working scripts; not referenced by tracked code |
| 5 | `reports/junit.xml` (2026-10-12, 1208 tests) | 148 KB | untracked | **Safe to remove** | Output of a local pytest run; `.github/workflows/ci.yml` regenerates it at this path on every CI run |
| 6 | `.git/claude-backup/` (working-file backups from 2026-10-13/14 sessions) | 830 KB | inside `.git` | **Needs Sandeep** (mostly removable) | Bundles `2d37ed1`, `7a73f21`, `c490393` and most file copies are already in history or on origin. Unique: `live_application.py.hardening-v1`, `live_application.py.wip-after-988203a`, `test_additional_instructions.py.v1` (intermediate drafts superseded by committed versions) plus git temp-pack leftovers. No stale lock is active in `.git` |
| 7 | 205 dated reports at the repository root (plus README, AGENTS, CLAUDE) | 1.1 MB | tracked | **Keep in place** | 54 are read or written by path by 18 tracked root helper scripts (`consolidate.py`, `read_mds.py`, `write_docs.py`, …); 77 are linked from other Markdown files (99 links); some are cited by path in frozen manifests (e.g. `experiments/phase15/PHASE15_FREEZE_MANIFEST.json`); `REAL_LLM_EVALUATION_PROTOCOL_V1_3.md` is pinned in `.gitattributes`. A move to `reports/archive/` would break those paths and recorded provenance. None is linked from README or `docs/` |
| 8 | `CI_FINAL_FORENSIC_AND_MODEL_SELECTION_REPORT.md`, `CI_MODEL_SELECTOR_FINAL_AUDIT.md` (2026-10-12) | 8 KB, 16 KB | untracked | **Needs Sandeep** | Researcher's CI reports; commit or keep locally |

Not reviewed as leftovers (Sandeep's known work or required tooling): `.env.example`, the 7 historical run/report files, both `TRACK_A_ANNOTATION_QA_V1` files, `track_a_annotation/ai_assisted/`, the untracked research outputs under `experiments/` and `reports/`, `reports/live_validation/runs/`, `.venv/`, `frontend/node_modules/`, and `.env` / `.env.local` (ignored, not opened).

**Space "Safe to remove" would free:** about **261 MB**.
- The three worktrees, 87 MB each.
- `reports/junit.xml` (148 KB), `redesign-upload-fix.bundle` (12 KB) and `.cursor/` (0 bytes).

The worktrees need `git worktree remove --force` because of their uncommitted files. That needs Sandeep's explicit go-ahead.

## Worktree detail

Each uncommitted file was compared with the repository by blob hash.
- `=HEAD` means identical to current HEAD.
- `blob in repo` means the content exists in some commit.
- `UNIQUE` means the content is in no commit.

**`acf08ee-fullsuite-wt` (base `c490393`)**
- UNIQUE: the 7 historical files (suite-rewritten).
- Everything else is `=HEAD` or `blob in repo`: `.env.example` equals the working copy; `live_application.py` and `test_vision_backend.py` are earlier committed versions.

**`acf08ee-fullsuite-wt2` (base `b5474ce`)**
- UNIQUE: the 7 historical files and `reports/audit/blocked_issue_register.md` (intermediate).
- Code files: `=HEAD` or `blob in repo`.

**`acf08ee-fullsuite-wt3` (base `bf29fe8`)**
- No UNIQUE files.
- The 7 historical files equal the working copy; the code files are `=HEAD` or `blob in repo`.
- The annotation folders are committed in `f58e8a8`.

Removing them loses no code. It loses only the simulation outputs the suite wrote and an intermediate register draft; the final register is committed.
