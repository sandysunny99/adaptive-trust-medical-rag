# Phase 3 cleanup record (2026-10-18 17:30 UTC, re-checked 2026-10-19)

Nothing tracked was deleted or moved. No user file was touched. Actions log: `phase3_cleanup_actions.txt`.

## Deleted (regenerable, untracked/ignored)
| Item | Why |
|---|---|
| `.pytest_cache/` (127 KB) | pytest cache, regenerated on the next run |
| `.ruff_cache/` (277 KB) | ruff cache |
| `frontend/dist/` (532 KB) | Vite build output, git-ignored, rebuilt by `npm run build` |
| 44 `__pycache__/` folders (outside `.venv` and `node_modules`) | bytecode caches |
| Worktrees `freeze-verify-bafc083`, `-a70c40e`, `-a70c40e-lf`, `-a0321d8`, `-9bae325` | Claude's clean, detached test copies (`git worktree remove`, no --force); their results are in the run folders |

## Investigate (left in place; owner decision needed)
| Item | Why not deleted |
|---|---|
| Worktrees `acf08ee-fullsuite-wt`, `-wt2`, `-wt3` | Claude's test copies, but each has uncommitted files (copied working-copy code and the 7 files the suite rewrote there); removal needs `--force`, which the rules forbid. Safe to remove with `git worktree remove --force` if Sandeep agrees |
| `continue-blockers.bundle`, `redesign-fixes.bundle`, `redesign-upload-fix.bundle` | branch bundles of unclear ownership; `continue-blockers.bundle` was the source for the BLK-010/BLK-011 ports |
| `claude-incoming/` | patch packages and the A/B/C kit used for validation |
| `cognee_service/` (incl. a HuggingFace model cache) | separate service, ownership unclear |
| `.cursor/`, `.playwright-mcp/`, `scratch/` | editor/tool state of unclear ownership |
| `reports/junit.xml` | generated test report, untracked; may be wanted by CI tooling |
| `.git/claude-backup/` (if present) | backups from earlier sessions |
| 208 dated audit reports at the repository root | historical evidence; archiving them into a folder would rewrite many paths and links, so it needs a separate decision |

## Keep (user work or research evidence)
`.env.example` and the 7 historical run/report files (uncommitted user edits), both `TRACK_A_ANNOTATION_QA_V1` files, `track_a_annotation/ai_assisted/`, `track_a_annotation/docs/` and `snapshots/`, untracked `experiments/annotations/v3_1_human/*` and `experiments/runs/f0-f1-*` outputs, `reports/phase2f5b/`, the four untracked `reports/live_validation/*_2026-10-1x.md` reports, and all `reports/live_validation/runs/` evidence.
