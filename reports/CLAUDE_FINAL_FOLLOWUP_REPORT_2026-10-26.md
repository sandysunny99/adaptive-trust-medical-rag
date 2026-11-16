# Final follow-up: CLI test hygiene and Linux gitleaks 8.21.2 (2026-10-26)

Research tool output only; nothing here is clinical advice.

## Summary

| Item | Result |
|---|---|
| `tests/test_cli.py` writing tracked experiment files | **Already fixed; no new code needed.** `5704c33` (2026-10-17) added `--run-dir` and a regression test. That commit is an ancestor of HEAD. The three modified `live-smoke-v1` files in the main checkout were last written on 2026-10-13, before the fix, so they are leftovers. |
| Any test writing into the repository | **None.** A fresh clone of the wip branch ran the full suite (1674 passed, 4 skipped, exit 0). Afterwards `git status --porcelain --untracked-files=all` was empty. |
| Linux gitleaks 8.21.2 | **Verified on Linux.** I ran the official linux_x64 binary in a Debian container (python:3.12-bookworm, Linux x86_64). It passed 27 of 27 real-binary checks, 168 of 168 security tests, 3 of 3 CI scripts, and 5 of 5 git-hook cases. |
| New commits this round | **None**, because neither item needed a code change |
| `.env` / `.env.local` | Not modified. Both were last written 2026-10-22 23:05, before this work. |
| Pushed | **No** |
| Frozen V1 corpus | SHA-256 `1FDB0BE65A1A2CF3D2847BF68FD6C5198C046760D44B23672F37DD9D78CA5578`, unchanged, git-clean |
| REL-LIVE-0004 | Still `UNGRADED`, no approver, outside `data/live_medical`. The gating tests pass. |

## 1. CLI output contamination

**Root cause.** Before `5704c33`, `research run` always wrote its run manifest, summary and per-case results into `experiments/runs/live-smoke-v1/`. That commit added a `--run-dir` option (the production default is unchanged) and pointed the tests at `tmp_path`. It also added `test_research_run_leaves_committed_artifacts_untouched`, which hashes the committed run and audit files before and after a run.

**Evidence today:**

| Check | Result |
|---|---|
| Hashes of the 3 working-tree files before and after `tests/test_cli.py` (20 passed) | Identical (`E6A62FA3…` manifest, `EE9C5201…` summary, `34783A1E…` case_results) |
| Last write time of those files | 2026-10-13 20:55, before `5704c33` |
| What changed in them | Only `executed_at`, `elapsed_seconds` and the `pytest-336` temp paths |
| Full suite in a fresh clone, then `git status` | Nothing changed, tracked or untracked |

**Not changed.** I left the three stale files in the main checkout as they are, as you instructed. Restoring them is your call:

```
git restore experiments/runs/live-smoke-v1/manifest.json experiments/runs/live-smoke-v1/summary.json experiments/runs/live-smoke-v1/case_results.jsonl
```

## 2. Linux gitleaks 8.21.2

**CI as configured** (`.github/workflows/ci.yml`, job `lint-and-test`):
- It runs on `ubuntu-latest` with Python 3.12 and sets `GITHUB_ACTIONS=true` and `TESTING=1`.
- It installs gitleaks with `curl -sSfL .../v8.21.2/gitleaks_8.21.2_linux_x64.tar.gz | tar -xz -C /usr/local/bin`. **It does not verify a checksum.**
- It runs `gitleaks detect` over the repository, the full pytest suite (which includes `test_gitleaks_unavailable.py`, the mocked failure states), and the hook check scripts.

**The binary I tested:**
- It is the same release asset CI downloads.
- SHA-256 `5bc41815076e6ed6ef8fbecc9d9b75bcae31f39029ceb55da08086315316e3ba` matches the release's `gitleaks_8.21.2_checksums.txt`.
- It ran in a throwaway `python:3.12-bookworm` container.
- The code under test is `fix/agent-guardrail-gaps` at `09ab153`. I cloned it inside the container, so it had LF line endings as in CI, and the repository was mounted read-only.

| # | Case | Result |
|---|---|---|
| 1 | Clean content, canonical scanner and CI copy | `CLEAN` |
| 2 | Synthetic token | `FINDINGS` |
| 3 | Raw token in any scan or gate output | absent |
| 4 | Invalid `.gitleaks.toml` | `UNAVAILABLE_OR_FAILED` (exit 1, no valid JSON report) |
| 5 | Real run with its report deleted, or replaced by malformed JSON | `UNAVAILABLE_OR_FAILED` (exit 0, no valid JSON report) |
| 6 | Claude gate | clean code: allow; token: deny; gitleaks missing: ask |
| 7 | Antigravity gate and its CI copy | clean code: allow; token: deny "SECRET DETECTED"; gitleaks missing: deny "COULD NOT RUN" |
| 8 | Git pre-commit hook in a temporary repo | clean file: committed. Token: blocked, with the token absent from output. gitleaks missing: blocked ("not installed", "not a found secret"). Invalid config: blocked ("could not complete"). |
| 9 | `CI=true` and `GITHUB_ACTIONS=true` with gitleaks missing | gates deny or ask; the hook blocks. Nothing is skipped or treated as clean. |
| 10 | CI copy vs canonical scanner | identical results in every case |
| — | Security test files on Linux | 168 passed |
| — | `check_secret_scan_allow.py`, `check_secret_scan_deny.py`, `check_hook_fail_closed.py` with `CI=true GITHUB_ACTIONS=true` | exit 0 each |

**What this does not cover.** The container is Debian bookworm, not the GitHub `ubuntu-latest` runner, and no remote workflow has run, because nothing was pushed. The binary, Python version and OS family match CI.

**Suggested hardening, not applied.** CI could verify the gitleaks download against the release checksum before installing it. That is a workflow change, so I left it for you to decide.

## 3. Safety invariants re-checked today

| Invariant | Evidence |
|---|---|
| Groq → Cloudflare, NVIDIA excluded | Built with `build_llm_router()` from the real config: `groq openai/gpt-oss-120b`, then `cloudflare @cf/meta/llama-3.3-70b-instruct-fp8-fast` |
| Placeholder sources rejected; no trust score without eligible evidence; REL-LIVE-0004 gated | `test_candidate_fixtures_are_gated.py`, `test_provider_decision_groq_cloudflare.py`, `e2e/test_live_source_links.py`, `e2e/test_live_evidence_provenance.py`, `e2e/test_live_warfarin_ibuprofen.py`, `test_frozen_hash_reproducibility.py`: **83 passed, exit 0** |
| Frozen V1 corpus | same SHA-256 as above; `git status -- data` is empty |
| No generated output in clinical records | The fixtures' manifests are `CANDIDATE_PENDING_RESEARCHER_APPROVAL`, and the fresh-clone run changed no file |

## 4. Git state

| Branch | HEAD | `git status --short` |
|---|---|---|
| `wip/pre-threads-20261022-1440` (main checkout) | `054cf16` | only the three stale `live-smoke-v1` files, reports, and your unrelated artifacts |
| `fix/agent-guardrail-gaps` | `09ab153` | clean |
| `claude/nostalgic-faraday-bff5f0` | `d64f68c` | clean |
| `claude/repair-skill-md-nul-bytes` | `d14656b` | clean |

## 5. Still open

- REL-LIVE-0004 needs a severity grade and approval from an authorized clinician or pharmacist.
- The CI workflow has not run remotely (nothing pushed).
- Optional: checksum verification in the CI gitleaks install step.
