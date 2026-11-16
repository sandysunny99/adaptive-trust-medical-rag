# Closure report: guardrails, MCP, skill integrity, providers, provenance (2026-10-24)

Research tool output only; nothing here is clinical advice.

**Confirmations**
- Nothing was pushed, tagged, amended, reset or rebased. All commits are local.
- `.env` and `.env.local` were not modified, copied or printed. Only variable names, set/empty status and allowlisted non-secret values (provider names, model IDs, flags) were read.
- The frozen `data/live_medical/LIVE_MEDICAL_CORPUS_V1.json` is unchanged (git clean; last commit `8b128e7`).
- The main checkout (`wip/pre-threads-20261022-1440`, `a96e171`) was only read; its uncommitted work was left as it was.

## A. Worktrees and commits

`core.hooksPath=.githooks` (from `.git/config`). In every worktree this resolves to the main checkout's `.githooks/pre-commit`; that wrapper runs `$(git rev-parse --show-toplevel)/.githooks/pre_commit_secret_scan.py`, so the scanner that ran for each commit is the committing worktree's own copy. The two wrappers differ only in line endings. The hook exits 0 when it runs with nothing staged (`git hook run pre-commit`).

| Branch | Start | Change | Local commit | Final `git status --short` | Pushed |
|---|---|---|---|---|---|
| `fix/agent-guardrail-gaps` | `d4b8c80` | Claude adapters ask when there is no command or no content to scan; parity tests; CI fail-closed check extended | `9089df1` | clean | No |
| `claude/nostalgic-faraday-bff5f0` | `354faeb` | Unknown MCP tool name no longer echoed (pending diff verified) | `78f8896` | clean | No |
| `claude/repair-skill-md-nul-bytes` | `f90936e` | Manifest reference tests (pending diff) plus invalid-structure handling and tests | `193d2f2` | clean | No |

Tool versions: uv 0.12.5, git 2.52.0.windows.1, gitleaks 8.30.1; Python, pytest and Ruff from each worktree's `uv` environment.

## B. Security regression matrix

Entry points are the real scripts run as subprocesses: `.claude/hooks/dangerous_command_gate.py`, `.claude/hooks/secret_write_gate.py`, `.agents/scripts/check_dangerous_cmd.py`, `.agents/scripts/pre_commit_secret_scan.py` (`tests/test_hook_adapter_parity.py`).

| Case | Expected (both gates) | Claude before fix | After fix |
|---|---|---|---|
| `{}` (command gate) | ask | **allow** | ask |
| `{"tool_input": {}}` | ask | **allow** | ask |
| empty command `""` | ask | **allow** | ask |
| blank command `"   "` | ask | **allow** | ask |
| null / list / number command | ask | ask | ask |
| empty stdin, malformed JSON, JSON array, JSON string | ask | ask | ask |
| `git status`, benign `find . -name "*.py"` | allow | allow | allow |
| recursive delete of `./build` | ask | ask | ask |
| recursive delete of `/` and of `./data` | deny | deny | deny |
| `{}` (secret gate) | ask | **allow** | ask |
| write with no content field | ask | **allow** | ask |
| non-text content | ask | **allow** | ask |
| malformed JSON (secret gate) | ask | ask | ask |
| empty content | allow | allow | allow |

Test-first evidence: before the fix the parity file reported **7 failed, 14 passed**; after it, **21 passed**.

Other guardrail checks on `9089df1`:

| Check | Result |
|---|---|
| Deny/ask lists vs base `4b6da3e` | DENY 21 → 25, ASK 15 → 24; every base rule kept, in order (recomputed from the files) |
| Destructive patterns (`find -delete`, `find -exec rm`, `xargs rm`, inline Python/Node deletes, encoded PowerShell, `data/` targets, benign near-misses) | `check_hook_deny.py` 12 deny, `check_hook_ask.py` 18 ask, `check_hook_allow.py` 11 allow; each runs both the Antigravity gate and the Claude adapter |
| Multi-replace `ReplacementChunks[].ReplacementContent` scanned; CI scanner copy runs the canonical scanner | covered in `tests/test_secret_scanner.py` (74 passed with the parity file) |
| Real gitleaks 8.30.1, canonical scanner | clean content → `[]`; synthetic GitHub-style token → 1 finding, raw value absent (redacted); malformed `.gitleaks.toml` → "GITLEAKS COULD NOT RUN (exit 1) … no valid JSON report", not clean |
| Commit-time hook | ran for `9089df1`, `193d2f2` and `78f8896` and passed |

## C. Test and CI evidence

All suites: `$env:TESTING='1'; uv run pytest -q` in the named worktree, exit code checked.

| Worktree | Command | Exit | Result |
|---|---|---|---|
| guardrail | full suite | 0 | **1833 passed, 4 skipped** (was 1812 + 21 new) |
| guardrail | `.agents/scripts/ci/check_*.py` (10 scripts) | 0 each | all OK |
| guardrail | `ruff check`, `ruff format --check` (changed files), `git diff --cached --check` | 0 | clean |
| guardrail | `gitleaks dir` on the 4 changed files | 0 | `[]` |
| MCP | `tests/test_mcp_server.py` | 0 | 156 passed |
| MCP | new test against the `354faeb` server | 1 | 1 failed (proves the test detects the echo); restored file hash identical |
| MCP | full suite, first run | -1073741510 | **interrupted** (Windows CTRL_C exit) during `test_single_worker_deployment.py` while two suites ran at once; not a test failure |
| MCP | full suite, second run (alone) | 1 | 1 failed, 1872 passed, 4 skipped: `test_provider_runtime_future_path.py::TestLocalPerformanceOverhead::test_full_success_path_overhead` measured 52 056 µs per call against a 1 000 µs (1 ms) per-call limit, i.e. 52 s for the 1 000-call loop (corrected; first written as "ms"); see CLAUDE_FOLLOWUP_REPORT_2026-10-24.md for the cause. It passed 3 of 3 times when rerun alone and does not touch `mcp_server.py` |
| MCP | full suite, third run (final bytes) | 0 | **1873 passed, 4 skipped**; commit made only after this run |
| MCP | `git diff --cached --check`, gitleaks on the 2 files | 0 | clean, `[]` |
| MCP | `ruff check` | 0 | clean |
| MCP | `ruff format --check` | 1 | pre-existing: the same findings exist in `354faeb`'s files; the pending diff adds none |
| skill | `tests/test_skill_md_integrity.py` | 0 | 8 passed |
| skill | full suite | 0 | **1725 passed, 4 skipped** |
| skill | ruff check, format check, diff check, gitleaks | 0 | clean |
| main checkout | `tests/e2e/test_live_warfarin_ibuprofen.py`, `test_live_source_links.py`, `test_live_evidence_provenance.py` | 0 | 51 passed |

The 4 skips are the same in every suite: `tests/test_provider_connectivity_preflight.py` (Groq, Gemini, HF, Cloudflare client initialisation, no live keys under `TESTING=1`). `uv lock --check` was not run: no dependency file changed.

## D. Provider configuration

Effective configuration, built with the real `load_env_files()` + `build_llm_router()` from the main checkout:

| Setting | Effective value | Source |
|---|---|---|
| `LLM_PROVIDER` | `groq` | `.env.local` (`.env` also sets it; `.env.local` wins, process env is unset) |
| `LLM_FALLBACK_PROVIDERS` | `cloudflare` | `.env.local` |
| `LLM_FAILOVER_ENABLED` | `true` | `.env.local` |
| `LLM_REQUEST_DEADLINE_S` | unset → 120 s | default |
| Router order | groq `openai/gpt-oss-120b` → cloudflare `@cf/meta/llama-3.3-70b-instruct-fp8-fast` | `build_llm_router()` |
| NVIDIA text | registered (`NVIDIA_API_KEY` alias set, `NVIDIA_LLM_API_KEY` unset), but filtered out of the order by `LLM_FALLBACK_PROVIDERS` | |
| `NVIDIA_LLM_MODEL` | unset → `nvidia/nemotron-3-super-120b-a12b` | code default |
| `CLOUDFLARE_ENABLED` | `false`, not read by the live router; Cloudflare is registered because token and account ID are set | |
| `LLM_FALLBACK_PROVIDER` (singular) | unset | |
| Vision | `nvidia_vision` `meta/llama-3.2-11b-vision-instruct` (`NVIDIA_OCR_API_KEY`), fallback `groq_vision/qwen/qwen3.8-27b` | startup log |
| Research-only keys (`GEMINI_API_KEY`, `HF_TOKEN`) | set, not registered in the live router | |

Dispositions:
1. **Provider order.** Not a defect in code: `.env.local` intentionally outranks `.env` (`api/app.py` `load_env_files`, `tests/test_live_provider_failover_policy.py`). Automatic routing never reaches NVIDIA because `LLM_FALLBACK_PROVIDERS=cloudflare`. If NVIDIA should be primary, the smallest change is in `.env.local`: `LLM_PROVIDER=nvidia` and `LLM_FALLBACK_PROVIDERS=groq,cloudflare`. Not applied; needs your authorization and a callable NVIDIA model first.
2. **`CLOUDFLARE_ENABLED`.** The repository documents it as not read by the live router (`docs/CONFIGURATION.md` line 42), and the main checkout's uncommitted `api/app.py` already logs a startup warning with a test (`tests/test_live_audit_regressions.py`). No code change made. To remove Cloudflare, unset its credentials in the active environment.
3. **NVIDIA 404.** The account's `GET /v1/models` returned 200 and lists `nvidia/nemotron-3-super-120b-a12b`; a minimal synthetic chat completion (`"Reply with the word ok."`, 5 tokens) to `https://integrate.api.nvidia.com/v1/chat/completions` returned **404**. The key authenticates (the model list works); the listed model is not callable on this endpoint for this account. No key was rotated and no model was substituted. Listed alternatives (`nvidia/nemotron-3-ultra-550b-a55b`, `nvidia/llama-3.1-nemotron-ultra-253b-v1`) were not tried.
4. **Key chains.** Text: `NVIDIA_LLM_API_KEY` → `NVIDIA_API_KEY`. Vision uses its own chain (`NVIDIA_OCR_API_KEY` set here); text availability does not imply vision availability.

## E. Medical RAG provenance

- `SPL-WARFARIN-001` and `SPL-IBUPROFEN-001` in the frozen V1 corpus carry `setid=example-warfarin` / `setid=example-ibuprofen`. `services/live_source_links.py` classifies `setid=example-` as a placeholder → `REJECTED_SOURCE_IDENTITY`; the eligibility loop excludes them before trust scoring, so no score is computed and the pre-LLM abstention runs. This is correct and unchanged.
- DailyMed's SPL service today: `example-warfarin` has 0 versions; warfarin set ID `884cdbf6-0a52-4126-8e14-b0d7c9367e33` resolves (8 versions; title "WARFARIN SODIUM (WARFARIN) TABLET [REMEDYREPACK INC.]").
- The 2026-10-22 work (`reports/live_validation/runs/2026-10-22-audit/CLAUDE_WARFARIN_IBUPROFEN_2026-10-22.md`) already built the pending REL-LIVE-0004 candidate from that label, kept outside the live folder and rejected while UNGRADED. Its 9 e2e tests are among the 51 that passed today; they cover placeholder rejection, a verified source passing identity, source identity vs claim support being separate, no score without eligible evidence, overstated claims withheld, and abstention without a relationship record.
- No new corpus version was created, no hash rewritten, and no trust score or medical claim was newly verified in this pass. The abstention is not a finding that the combination is safe.

## F. Outstanding items

| Category | Item |
|---|---|
| Deferred change requiring authorization | Choose the primary provider; if NVIDIA, edit `.env.local` as in D.1 after a callable model is confirmed. |
| Environment / external service | `nvidia/nemotron-3-super-120b-a12b` is listed for the account but chat returns 404. |
| Deferred change requiring authorization | REL-LIVE-0004 needs a severity grade and your approval; the ibuprofen label (`72ec2491-…`) has run-together XML text and cannot ground a record. |
| Unverified behavior | When the gitleaks binary is missing, `scan_with_gitleaks` returns `[]`, so the Claude and Antigravity write gates fall back to regex-only without asking (the git hook does report it loudly). This was the design in `d4b8c80`; changing it to "ask" is a policy decision left to you. |
| Unverified behavior | The main checkout's uncommitted work (provider warnings, provenance tests, REL-LIVE-0004 candidate) is not committed on any branch. |
| Unverified behavior | `TestLocalPerformanceOverhead::test_full_success_path_overhead` is a wall-clock test that failed once under load (52 s stall) and passed on every rerun; it can fail spuriously on a busy machine. |
| Confirmed defect (pre-existing) | `ruff format --check` fails on `.agents/scripts/mcp_server.py` and `tests/test_mcp_server.py` at `354faeb`; untouched to keep the MCP commit minimal. |
