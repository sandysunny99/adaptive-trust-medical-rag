# Follow-up report: gitleaks, test reliability, SPL text, provider decision (2026-10-24)

Research tool output only; nothing here is clinical advice.

## 1. Executive status

**Acceptance checks**

| # | Check | Result |
|---|---|---|
| 1 | A missing or failed gitleaks scan can't be mistaken for a clean scan, and the Claude and Antigravity gates stay consistent | **Fixed and test-verified** (`4dc5e26`). Before the fix, the real gates allowed clean code when gitleaks was missing; 37 of 42 new tests failed. After it: Antigravity denies ("SECRET SCAN COULD NOT RUN"), Claude asks, and the git hook blocks. Neither gate allows. |
| 2 | Full suites pass on the final code, including the stalled performance test | Guardrail branch: **1878 passed, 4 skipped, exit 0**. MCP branch: **1873 of 1873** passed, split across two processes (§7). Main checkout working tree: **1666 passed, exit 0**. The performance stall is diagnosed and fixed (`e26f9c3`). |
| 3 | V1 corpus unchanged, placeholders rejected, REL-LIVE-0004 gated | V1 SHA-256 is `1FDB0BE6…78CA5578`, git-clean, and was last changed in `8b128e7`. The placeholder and gating tests pass (§4). REL-LIVE-0004 is still UNGRADED and outside `data/live_medical`. |
| 4 | Every change committed locally, hooks pass, status reported, nothing pushed | There are 7 new local commits (§8). The secret hook passed on each one. Nothing was pushed. Your pre-existing uncommitted work is preserved (§8.2). |

**Fixed and verified by tests:** the missing-gitleaks fail-open; the stalled performance test; full-suite runs killed by uvicorn's CTRL_BREAK; SPL block elements running together; MCP formatting.
**Characterised, no defect found:** Groq → Cloudflare routing (9 new tests).
**Unresolved or needs approval:** see §9.

## 2. Gitleaks failure matrix

The scanner now reports one of three explicit states: `CLEAN`, `FINDINGS` or `UNAVAILABLE_OR_FAILED`. `scan_with_gitleaks()` returns `[]` only for `CLEAN`. Tests are in `tests/test_gitleaks_unavailable.py` (42), plus the existing `test_ci_secret_scan_gitleaks.py` and `test_secret_scanner.py`.

| Scenario | State | Antigravity gate | Claude gate | Git hook | Before the fix |
|---|---|---|---|---|---|
| Valid empty report, exit 0 | CLEAN | allow | allow | pass | same |
| Findings report | FINDINGS | deny "SECRET DETECTED" | deny | block | same |
| Binary missing | UNAVAILABLE | **deny** "COULD NOT RUN" | **ask** | **block** | **allow / allow / pass with warning** |
| `CI` or `GITHUB_ACTIONS` set | the scan runs | as above | as above | n/a | **skipped and treated as clean** |
| Start error, permission error | UNAVAILABLE | deny | ask | block | same |
| Timeout | UNAVAILABLE | deny | ask | block | same |
| Bad config (exit 1, no report) | UNAVAILABLE | deny | ask | block | same |
| Exit 0 with missing, malformed or non-list report | UNAVAILABLE | deny | ask | block | same |
| Exit 1 with an empty report | UNAVAILABLE | deny | ask | block | same |
| Regex secret, gitleaks missing | n/a | deny "SECRET DETECTED" | deny | block | same |
| Regex secret, gitleaks clean | n/a | deny "SECRET DETECTED" | deny | block | same |

- **Real entry points:** I ran the scripts as subprocesses with gitleaks removed from PATH, with and without `CI` / `GITHUB_ACTIONS`. Claude returned `ask` and both Antigravity copies returned `deny`. Before the fix all three returned `allow`.
- **Real gitleaks 8.30.1:** clean content gave CLEAN; a synthetic token gave FINDINGS, and the raw value did not appear in the output; a malformed `.gitleaks.toml` gave UNAVAILABLE (exit 1, no valid JSON report).
- **Antigravity vs Claude:** a failed scan denies in Antigravity and asks in Claude. These are the contracts `d4b8c80` set for each gate. Both fail closed, and neither treats a failed scan as a found secret.
- **CI scripts:** all 10 `.agents/scripts/ci/check_*.py` checks exit 0. `check_secret_scan_allow` and `check_secret_scan_deny` also pass with `GITHUB_ACTIONS=true`.
- **Not verified:** GitHub's runner installs gitleaks 8.21.2. I could only run 8.30.1 locally.
- **Contract change:** the git hook now blocks a commit when gitleaks is missing (it used to warn). `docs/TESTING.md` documents this.

## 3. Performance investigation

**What failed.** `test_full_success_path_overhead` reported 52,056 µs per call against a 1,000 µs per-call limit, which is 52 s for a 1,000-call loop. My first report said "52,056 ms"; that was a unit error and is now corrected there. The code under test is pure Python with no I/O or locks. It normally takes 2.7 to 5.3 µs per call (10 measurements today).

**Cause.** The Windows System log shows Kernel-Power 506 (Modern Standby entered) at 16:49:08 and 507 (exited) at 16:55:14. That falls inside the run from 16:47:46 to 16:56:27. A wall-clock loop counts the time the process was suspended.

**Fix (`e26f9c3`).** The test now times five batches and keeps the fastest. The thresholds are unchanged. Two new tests check the measurement itself:
- a call that really is slow is still reported as slow;
- one stalled batch no longer fails a fast path. With the old single loop, the same stall gave 1,200 µs per call.

**Prevention.** I asked the app to keep the machine awake while suites run. Standby happened twice more during this session (16:34 to 16:37 and 17:31 to 17:32).

**Second, unrelated interruption: the suite killed with exit 0xC000013A.** This happened in 4 runs, always in `test_the_same_command_with_two_workers_refuses_to_start[WEB_CONCURRENCY=2]`.
- **Cause:** when a worker refuses to start, uvicorn 0.54 stops a worker that is still running with `os.kill(pid, CTRL_BREAK_EVENT)` (`uvicorn/supervisors/multiprocess.py:107`). That worker doesn't lead a process group, so Windows sends the event to every process on the console, pytest included.
- **Reproduced:** a parent process that started such a child without its own console exited with 0xC000013A. With `CREATE_NO_WINDOW` it survived.
- **Fix (`761bccd`):** the test now starts the server in its own hidden console, and a regression test covers it. The fix is on the guardrail branch only. The MCP branch still has the old test, so its suite ran the two-worker test as a separate process (§7). The main checkout's branch does not have this test.

## 4. SPL text and provenance

**Extraction defect fixed (`76df3f2`).** `text_of()` joined every text node with nothing between them. Paragraphs, list items, table cells, titles and `<br/>` therefore ran together whenever there was no whitespace between their tags. 7 of 11 new tests failed before the fix. Inline markup still joins as written, and a missing node now gives `""` instead of crashing. I checked the fix against the existing candidates: all three candidate sections extract to the same text and SHA-256 as their committed files (lisinopril `34ebeea1` v12 sections 7.1 and 5.5; warfarin `884cdbf6` v8 section 7.3). No candidate hash changes.

**The ibuprofen problem is in the source data, not the parser.** Label `72ec2491-924d-460f-9510-62d624d54b59` (v17, effective 2026-05-13) has "Ibuprofentablets", "otherclotting" and similar run-together words inside a single XML text node. No parser can recover that without inventing text, so the extractor keeps it as published, and a test pins that behaviour.

**Verified alternative ibuprofen sources.** I checked these with the DailyMed SPL service; they are not used anywhere yet:

| Set ID | Version (latest?) | Effective | Labeler | Active moiety | Section | Text check |
|---|---|---|---|---|---|---|
| `b7e4f477-82b5-4c5c-8d3e-99c48cc090f4` | 2 (yes) | 2026-10-01 | Proficient Rx LP | IBUPROFEN | "Warfarin-type anticoagulants", 688 chars, SHA-256 `2b48c7ca9f46f62b…` | names ibuprofen and warfarin as whole words; no run-together tokens |
| `404df13d-4ada-4324-9eed-e21f5d5043a4` | 6 (yes) | 2026-10-15 | REMEDYREPACK INC. | IBUPROFEN | same title, 688 chars, `1f9d10d08f4a9504…` | same |

For each one I checked that the `setId` matches, that the version is the latest in its history, and the title and active moiety. That establishes source identity only. Whether the section supports a particular interaction claim is a separate check that needs human review: the section reports that controlled studies did not show an effect on prothrombin times, and also reports bleeding and synergistic GI-bleeding risk.

**REL-LIVE-0004 is still gated.**
- It is grounded on the warfarin label `884cdbf6` v8 section 7.3; the chunk hash is unchanged at `23081251…`.
- Severity is UNGRADED, nothing is approved, and it is not in `data/live_medical`.
- What it needs to go further: a severity grade by your documented method, a named approver, and a copy into its own V2 folder with new hashes.

**Pipeline invariants** were covered by tests in the main checkout's working tree:
- placeholder `setid=example-` links are rejected before trust scoring;
- no eligible evidence means abstention;
- an UNGRADED record is rejected even with an approved manifest;
- source identity and claim support are separate checks.

The test files are `test_live_warfarin_ibuprofen.py`, `test_live_source_links.py`, `test_live_evidence_provenance.py` and `test_live_audit_regressions.py`. Results are in §7.

## 5. Provider tests (`6b1d4dd`)

`tests/test_provider_decision_groq_cloudflare.py` has 9 tests. They build the router with `build_llm_router()` using the decided configuration, and an NVIDIA key is present in every case.

| Behaviour | Result |
|---|---|
| Order | groq `openai/gpt-oss-120b` → cloudflare `@cf/meta/llama-3.3-70b-instruct-fp8-fast`; NVIDIA is registered but not in the order |
| Groq answers | neither Cloudflare nor NVIDIA is called |
| Groq timeout, 404, 401 or schema error | fails over to Cloudflare only |
| Groq and Cloudflare both fail | the request errors; NVIDIA is never called |
| Groq hangs past a 0.3 s deadline | the whole request finishes in under 2 s; NVIDIA is never called |
| `CLOUDFLARE_ENABLED=false` | Cloudflare stays registered; the ignored flag is logged |

- These tests describe current behaviour; I found no defect.
- Per-provider retry policy, manual selection with no failover, and log redaction were already covered by `test_live_provider_failover_policy.py` and `test_router_failover.py`.
- **NVIDIA:** no change. The earlier 404 on `nvidia/nemotron-3-super-120b-a12b` stands, and NVIDIA stays out of automatic routing.
- **`.env` and `.env.local` modified: No.**

## 6. Formatting and skills

- **MCP (`c99b2e3`):** formatting only, 13 lines added and 7 removed. The AST of both files is identical before and after. `ruff format --check` now passes; it failed at `354faeb`.
- **Skill integrity:** no new defect. `tests/test_skill_md_integrity.py` passes 8 of 8 on `193d2f2`: thresholds 0.30 / 0.45 / 0.60 / 0.75, the NUL/BOM check, manifest references, and invalid manifest structure.
- **Pre-existing formatting failures I left alone:** `.githooks/pre_commit_secret_scan.py`, `tests/test_provider_runtime_future_path.py` and `tests/test_single_worker_deployment.py` already fail `ruff format --check` at their base revision. I changed only the lines the fixes needed. `ruff check` is clean on every changed file.

## 7. Verification evidence

All runs use `$env:TESTING='1'; uv run pytest -q`, one suite at a time.

| Where | Run | Exit | Result |
|---|---|---|---|
| guardrail, new gitleaks tests before the fix | `tests/test_gitleaks_unavailable.py` | 1 | 37 failed, 5 passed |
| guardrail, targeted after the fix | gitleaks, secret scanner and parity tests | 0 | 168 passed |
| guardrail, full suite (2nd run today) | full | -1073741510 | interrupted by the CTRL_BREAK issue (§3) |
| guardrail, full suite on final bytes | full | 0 | **1878 passed, 4 skipped** |
| guardrail | 10 CI check scripts | 0 each | OK |
| MCP, full suite run 4 | full | -1073741510 | interrupted (CTRL_BREAK, old test) |
| MCP, final bytes | full, two-worker test deselected | 0 | **1871 passed, 4 skipped, 2 deselected** |
| MCP, final bytes | the 2 deselected tests, run separately | 0 (3 of 3 attempts) | 2 passed each time; one earlier separate attempt was interrupted the same way |
| skill | `tests/test_skill_md_integrity.py` | 0 | 8 passed |
| wip branch, exact commit tree (`git checkout-index` export) | full | 1 | 1567 passed, 10 failed, 4 errors. Plain `HEAD` exported the same way fails the same 9 tests with the same 4 errors (no `.git`, and git-ignored candidate files missing in an export), so the export causes them. The 10th failure was my deadline test; I fixed its race and it then passed 5 of 5. |
| wip branch, export | `tests/test_spl_text_extraction.py`, `tests/test_provider_decision_groq_cloudflare.py` | 0 | 20 passed |
| main checkout working tree (your uncommitted work, plus `76df3f2` and `6b1d4dd`) | full | 0 | **1666 passed**. This branch has no two-worker deployment test, so nothing was deselected. The Medical RAG provenance tests in §4 ran as part of this suite. |

`uv lock --check` was not run because no dependency files changed. gitleaks reported no findings on every committed file set, and `git diff --cached --check` was clean for every commit.

## 8. Git state

### 8.1 Commits (all local; push status: **No**)

| Branch | Start | New commits | Final `git status --short` | Hook |
|---|---|---|---|---|
| `fix/agent-guardrail-gaps` | `9089df1` | `4dc5e26` gitleaks states; `e26f9c3` perf measurement; `761bccd` uvicorn console | clean | passed ×3 |
| `claude/nostalgic-faraday-bff5f0` | `78f8896` | `c99b2e3` formatting | clean | passed |
| `claude/repair-skill-md-nul-bytes` | `193d2f2` | none | clean | n/a |
| `wip/pre-threads-20261022-1440` (main checkout) | `a96e171` | `76df3f2` SPL text; `6b1d4dd` routing tests | your pre-existing changes, unchanged (below) | passed ×2 |

I committed `76df3f2` by staging only the `text_of` hunk. Your separate uncommitted `how_to_approve` edit in the same file (6 lines) is still unstaged.

**Correction to my last report:** the provider startup warnings were already committed in `a96e171`. They were not uncommitted work.

### 8.2 Your uncommitted work in the main checkout (preserved, not committed)

| Group | Files | Classification |
|---|---|---|
| Multi-dataset relationship loading, claim strength, OCR and cancel lifecycle, upstream error bodies kept out of user messages | `services/live_application.py`, `live_relationships.py`, `claim_strength.py` (new), `canonical_identity.py`, `api/routes/analyze.py`, `ingest.py`, `llm_backend/*` (5 files), and their tests (`test_live_multi_dataset_loading.py`, `test_claim_strength.py`, `test_vision_fallback_and_timeouts.py`, `test_api.py`, e2e changes) | Useful, but one interdependent feature set that needs its own review before committing |
| Frontend result and evidence display | 9 files under `frontend/src` | Useful; needs review with the backend changes |
| Relationship candidates and builders | `scripts/build_rel_live_0004_candidate.py`, `build_food_0001_candidate.py` (new), `tests/fixtures/*_candidate/`, `test_live_warfarin_ibuprofen.py`, the `how_to_approve` edit | Pending clinical approval. Do not commit as approved. |
| Experiment outputs | `experiments/runs/live-smoke-v1/*` | Regenerated run artifacts; needs review against the protected baselines |
| Configuration template | `.env.example` | Placeholder template; useful but needs review |
| Unrelated artifacts | `*.bundle`, `cognee_service/`, `claude-incoming/`, `track_a_annotation/ai_assisted/`, `reports/junit.xml`, `reports/live_validation/runs/` | Unrelated user work and reports; left alone |

Committed tests on `a96e171` depend on files that are not committed, such as the `rel_live_0003_candidate` folder under `reports/live_validation/runs/`. That is why a clean export of the commit fails 13 of them.

## 9. Remaining blockers

| Category | Item |
|---|---|
| Approval required | REL-LIVE-0004 severity grade and named approver. Whether to build a candidate from ibuprofen label `b7e4f477…` or `404df13d…`. |
| Approval required | Whether and how to commit the main-checkout feature set (§8.2). |
| External service | NVIDIA `nemotron-3-super-120b-a12b` returns 404 on chat completions for this account. NVIDIA stays out of routing. |
| Unverified | gitleaks 8.21.2 on GitHub's runner with the CI skip removed. Locally verified with 8.30.1 only. |
| Pre-existing defect, fixed on one branch | The uvicorn CTRL_BREAK test hazard is fixed only on `fix/agent-guardrail-gaps`. The MCP and skill-integrity branches still carry the old test. |
| Pre-existing | Formatting in the three files listed in §6. |
| Pre-existing | Tests at `a96e171` depend on files that are not committed (§8.2). |
| Environment | Modern Standby suspends suites. Keep the machine awake (or plugged in with standby off) during long runs. |
