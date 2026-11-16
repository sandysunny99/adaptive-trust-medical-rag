# Repository audit, cleanup, documentation and GitHub synchronization — final report

This covers Sandeep's master task of 2026-10-18 17:14 UTC. Work ran 2026-10-18 17:15 to 17:32 UTC and 2026-10-19 05:32 to 06:30 UTC; the PC was offline in between. Evidence is in this folder.

## Repository and SHAs

| Item | Value |
|---|---|
| Repository | `sandysunny99/adaptive-trust-medical-rag`, local `C:\Users\sunny\Downloads\CASE STUDY` |
| Branch | `ui/3d-redesign` (no branch change) |
| Starting HEAD | `9bae325` (11 commits ahead of origin) |
| Remote before | `c490393` |
| Remote after the checkpoint push (2026-10-18) | `9bae325` |
| Final HEAD = final remote | `baf6c93` |
| Tags / release / deployment | none created, none pushed |

All pushes were normal fast-forwards. There was no force-push, rewrite, amend, reset, stash, rebase or `git clean`.

## Security and publication audit

**Checkpoint, 11 commits `c490393..9bae325`, 39 files, +5908/-147**
- gitleaks (with `.gitleaks.toml`) found no leaks in the range, in the whole branch history (161 MB) or in the current uncommitted changes.
- No env, credential or key files are in the range. The only tracked env file is the `.env.example` template, which was not opened.
- No ignored file is tracked.
- Frozen corpus, `data/`, prompts, verification, trust scoring and recorded frozen hashes: unchanged by the range. The one exception is the reviewed V2 loader in `services/live_relationships.py`.
- No historical run evidence was removed or overwritten.
- Evidence: `phase2_publication_audit.txt`, `phase2_current_changes_scan.txt`, `phase2_checkpoint_push.txt`.

**Final range, 2 commits `9bae325..baf6c93`, documentation only**
- 6 files, no code, data or test changes.
- gitleaks: no leaks. Evidence: `phase9_final_push.txt`.

## Cleanup (details in `PHASE3_CLEANUP_RECORD.md`, log in `phase3_cleanup_actions.txt`)

**Deleted** (untracked or git-ignored, regenerable):
- `.pytest_cache/`, `.ruff_cache/`, `frontend/dist/` and 44 `__pycache__/` folders;
- Claude's clean test worktrees `freeze-verify-bafc083`, `-a70c40e`, `-a70c40e-lf`, `-a0321d8`, `-9bae325`, `verify-6b1695d`, `-lf`, `verify-baf6c93`, `-lf` (`git worktree remove`, no `--force`).

**Nothing tracked was deleted or moved**, so there is no cleanup commit.

**Investigate** (left for Sandeep):
- worktrees `acf08ee-fullsuite-wt`, `-wt2`, `-wt3` (uncommitted copies; removal needs `--force`);
- the three `.bundle` files, `claude-incoming/`, `cognee_service/`, `.cursor/`, `.playwright-mcp/`, `scratch/`, `reports/junit.xml`, any `.git/claude-backup/`;
- the 208 dated audit reports at the repository root (archiving would rewrite many paths).

## Documentation (commits `6b1695d`, `baf6c93`)

| File | Change |
|---|---|
| `README.md` | Rewritten for the current code. It now has: an implementation-status table (implemented / pending approval / blocked); the live pipeline and dual safety gates; evidence sources with their real status; providers as registered (NVIDIA, Groq, Cloudflare; Hugging Face, Gemini and FreeLLMAPI are research-harness only); setup; tests; security; REST API; CLI with the parser's real syntax; ablation variants; limitations. The A–F scorecard is replaced by a statement that no empirical scorecard exists yet: those tables are simulation output (`MockVariantPipeline`) |
| `docs/ARCHITECTURE.md` | Covers: the live pipeline as implemented (endpoints, stages, modules, SSE events, error codes); the dual safety gates with the real nine-factor trust calculation and per-tier weights from `config/trust.yaml`; relationship records; frontend; the research harness and optional database; threat model; research integrity policy; differences from the earlier version (gate order, in-memory 384-dimensional retrieval rather than pgvector 768, the trust formula) |
| `docs/CONFIGURATION.md` (new) | Requirements, install, environment variables (names from the source, placeholders only, live app versus research harness), run commands, troubleshooting |
| `docs/TESTING.md` (new) | Every suite and scan, exact-build and LF-checkout procedures, browser scenarios, latest verified results |
| `docs/architecture/INTEGRATION_ROADMAP.md` | Marked historical (2026-09-05); points to the register |
| `reports/audit/blocked_issue_register.md` | Entries from 2026-10-15 to 10-19; commits now marked pushed; REL-LIVE-0001/0002 stay pending |

- **Checks:** every relative link and every code path named in the four main documents exists (0 problems). The project has no link checker of its own.
- **Doc tests:** `tests/test_docs.py` failed on `6b1695d` (5 required section names missing). This was fixed in `baf6c93` by adding the sections with current content. The tests were not changed.

## Verification of the final candidate `baf6c93`

Fresh worktrees with nothing uncommitted. `baf6c93` has no code, test or data change from `9bae325`.

| Check | Result |
|---|---|
| Full backend suite (Windows checkout) | **1470 passed, 4 skipped, 0 failed** (exit 0) |
| 7 historical files, sha256 before vs after | identical |
| `git status` before, after and after checks | clean |
| ruff | clean |
| `run_bandit.py` | exit 0 |
| gitleaks `9bae325..baf6c93`; hook allow/deny | no leaks; OK, OK |
| `verify_v3_1_integrity`, `verify_v3_confirmed_separation` | PASS, PASS |
| `audit_frozen_hash_line_endings.py --check` | 311 CRLF-recorded files, 0 unpinned |
| Linux-style checkout (`core.autocrlf=false`, `core.eol=lf`): frozen-hash, prompt-hash, annotation, CLI, vision, doc tests | **111 passed**; audit and integrity clean |
| Frontend (2026-10-19, frontend unchanged) | 15 files, **93 passed** (first attempt hit a worker start-up timeout under low memory, kept as `frontend/vitest_attempt1_worker_start_timeout.txt`; rerun with one worker passed); build OK; lint 0 errors, 3 warnings |
| Superseded run `6b1695d` | 1465 passed, 5 failed (doc tests), kept in `phase7_6b1695d_superseded_doc_tests_failed/` |
| Sandeep's working-copy 7 files | unchanged |

## Known issues, verified against today's evidence

1. **NVIDIA timeouts:** NVIDIA's answer model timed out in automatic mode (2 timeouts in the `9bae325` browser runs; 4 of 4 auto-mode calls on 2026-10-18), and Groq answered after failover. It answered every time it was selected directly. **Open.**
2. **Disclaimer residue:** disclaimer wording remains in claim 0 of 3 of the 4 `9bae325` browser runs, with `removed_disclaimers: []`. Those claims are withheld. **Open.**
3. **Relationship records:** REL-LIVE-0001 and both REL-LIVE-0002 revisions are `CANDIDATE_PENDING_RESEARCHER_APPROVAL`, and nothing V2 is in `data/`. EVIDENCE_BACKED_ANSWER_VERIFIED stays **NO**.

**Difference from earlier reports:** the README previously described the project as "functionally complete" and showed simulated A–F metrics with significance claims. Both are corrected. No measured results changed.

## Remaining uncommitted work (Sandeep's; intentionally not published)

- `.env.example` and the 7 historical run/report files.
- Both `TRACK_A_ANNOTATION_QA_V1` files and `track_a_annotation/ai_assisted/`.
- Untracked reports, bundles, `claude-incoming/`, `cognee_service/`, untracked research outputs under `experiments/`, and all `reports/live_validation/runs/` evidence, including this audit folder.

## Statuses (kept separate)

| Status | Value |
|---|---|
| GitHub branch synchronization | **Synchronized**: `origin/ui/3d-redesign` = local HEAD = `baf6c93` |
| Release / tag / deployment | **None** |
| EVIDENCE_BACKED_ANSWER_VERIFIED | **NO** (no approved relationship record) |
| APPLICATION_FREEZE_READY | **Not declared**: Sandeep's decision |

**Freeze recommendation, for Sandeep to decide.** For a *safe-abstention-only* freeze, the evidence now supports YES:
- the exact committed build passes all automated checks on Windows and on an LF checkout;
- every browser scenario (A on `a0321d8`; B, C, N1, N2 on `9bae325`, which has the same source) behaved as required;
- documentation now matches the code.

The remaining open items are the NVIDIA auto-mode timeouts and the disclaimer residue; neither releases unsafe content. An evidence-backed-answer freeze is not possible until a relationship record is approved and tested end to end.

## Manual review needed

- Sandeep's review of the new README and docs.
- Decisions on the "Investigate" items.
- The freeze call.
- REL-LIVE-0002 approval (approver name and date).
