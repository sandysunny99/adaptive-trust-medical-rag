# Exact-build check and browser runs, 2026-10-18

Evidence: `followup_2026-10-18/`. No existing run file was overwritten.
- Not done: no push, no tag, nothing staged.
- Untouched:
  - REL-LIVE-0001 and REL-LIVE-0002 stay pending, and `data/live_medical/relationships/` is untouched.
  - Sandeep's NVIDIA edits stay uncommitted.
  - Sandeep's working copy and servers were not touched. His servers were no longer listening on 8000/5173; Docker held those ports.

## New local commits

| Commit | Content | Staged diff |
|---|---|---|
| `c71ed1f` | fix: make frozen artifact hashes reproduce on LF checkouts (BLK-010, ported from `d8e44c3` without its Cognee changes) | 4 files, +145/-6: root `.gitattributes` UTF-16 → UTF-8 (33,293 bytes); new `scripts/audit_frozen_hash_line_endings.py`; new `tests/test_frozen_hash_reproducibility.py`; the folder `.gitattributes` removed (its 3 pins are in the root file) |
| `a70c40e` | fix: pin the LF-hashed Phase 2f5 runner so its frozen hash reproduces on Windows | 1 file, +2 |

- **Why `a70c40e` exists:** the first exact-build run of `c71ed1f` (kept in `exact_build_c71ed1f_superseded/`) failed one test. `runner_real_hardened.py` is recorded as LF (`774c9d65…`), and nothing pinned it, so a Windows autocrlf checkout wrote CRLF. It is now pinned `text eol=lf`.
- **Timing:** this commit was made before the coordinator's 09:52 UTC note asking for no new commits arrived.
- **Effect on Sandeep's copy:** for both commits, every file under a line-ending rule was hashed through the new rules (`git hash-object --path`) against its stored blob. None of them changed git's view of his working copy, and `git status` is identical to before.

### `REAL_LLM_EVALUATION_PROMPT_V1_2.txt`

| Rule | Fresh checkout | Sandeep's CRLF working copy | Chosen |
|---|---|---|---|
| `-text` (the bundle's rule) | LF = recorded hash `e5aeb4fa…` | hashes to `edafeaf2…` ≠ blob, so **shows as modified** | no |
| `text eol=lf` | LF = recorded hash | hashes to the blob `45026b54…`, so **unmodified** | **yes** |

His file was not rewritten (sha256 `f876e4d2…` before and after).

## Exact build `a70c40e`

Fresh worktree `C:\Users\sunny\freeze-verify-a70c40e`, with nothing uncommitted.

| Check | Result |
|---|---|
| Full backend suite (`TESTING=1 pytest -q`) | **1454 passed, 4 skipped, 0 failed** (exit 0, 300 s) |
| 7 historical files, sha256 before vs after | identical |
| `git status` before and after | clean |
| ruff `src/ tests/` + audit script | clean |
| `run_bandit.py` | exit 0 |
| `audit_frozen_hash_line_endings.py --check` | 311 CRLF-recorded files, 0 unpinned |
| Integrity scripts | PASS, PASS |
| Hook allow/deny | OK, OK |
| gitleaks over `bafc083..a70c40e` | no leaks |
| Frontend | unchanged since `bafc083` (93 tests, build and lint passed there) |

## LF checkout (Linux CI emulation)

The worktree `C:\Users\sunny\freeze-verify-a70c40e-lf` was created with `core.autocrlf=false` and `core.eol=lf`.
- **Line endings it got:** unpinned files come out LF (for example `cli.py`). Pinned files come out as recorded: the REAL_LLM prompt and the runner LF, the adjudication prompt and the CRLF-recorded artifacts CRLF.
- **Tests:** the frozen-hash, prompt-hash, annotation and CLI tests pass, **72 of 72**.
- **Audit and integrity:** `audit --check` passes (0 unpinned), both integrity scripts pass, and `git status` is clean.

## Browser runs on `a70c40e` (kit v2)

**Setup**
- The backend ran on 127.0.0.1:8010 from the worktree's code. The launcher logged "exact-build code: C:/Users/sunny/freeze-verify-a70c40e/src/...".
- Credentials: `followup_2026-10-18/browser/run_exact_build_backend.py` loads the repo's `.env.local` and then `.env` into the backend process only, in the order the app uses, with `override=False`. Nothing was printed, logged or copied.
- The first start hit a momentary bind conflict on 8010 (kept as `backend_attempt1_port_in_use.log`).
- The frontend ran on 127.0.0.1:5180 from the worktree, with a temporary untracked config proxying to 8010. `node_modules` was a junction; both were removed afterwards.
- `/health` returned 200 with `mode: test`, as before. The catalog offered nvidia, groq and cloudflare, so B-NV was run.
- Memory was low throughout (about 0.3–0.6 GB free of 15.8 GB, mostly other applications). No run failed for resource reasons.

| Run | Selection | Served by (from the stream) | embedding_mode | Retrieved / eligible / unrelated | Tier | Terminal |
|---|---|---|---|---|---|---|
| A-image | auto | none | n/a | n/a | n/a | **error VISION_EXTRACTION_ERROR** "Vision provider failed to return valid JSON" (nvidia_vision / meta/llama-3.2-11b-vision-instruct) |
| A-image-retry1 | auto | none | n/a | n/a | n/a | same error |
| B-direct-cloudflare | manual cloudflare | cloudflare / @cf/meta/llama-3.3-70b-instruct-fp8-fast, stop, 1702 chars | real (MiniLM) | 14 / 1 / 13 | R2 0.60 | abstention, 8 of 8 claims withheld |
| B-direct-nvidia | manual nvidia | nvidia / nvidia/nemotron-3-super-120b-a12b, stop, 1321 chars | real | 14 / 1 / 13 | R2 0.60 | abstention, 6 of 6 withheld |
| C-context | auto | groq / openai/gpt-oss-120b, stop (NVIDIA timed out first) | real | 14 / 1 / 13 | R2 0.60 | abstention, 6 of 6 withheld |
| N1-note-policy | auto | groq / openai/gpt-oss-120b, stop (NVIDIA timed out first) | real | 14 / 1 / 13 | R2 0.60 | abstention, 6 of 6 withheld |
| N2-note-injection | auto | none | n/a | n/a | n/a | error INPUT_REJECTED (log: marker name and length only) |

- **Retrieval:** `relationship_evidence_chunks` is `[]` in every retrieval event, so REL-LIVE-0002 is not loaded, as expected.
- **Credentials:** none found in the scenario folder.
- **Why scenario A fails here:** the committed `openai_vision_backend.py` parses the reply with a plain `json.loads`. The code-fence stripping and schema validation (`NVIDIA_VISION_SCHEMA_REMEDIATION_2026-10-12.md`) exist only in Sandeep's uncommitted edits. The 2026-10-15 runs, which included those edits, extracted the image successfully. **No committed revision has a working image path yet.**

## Freeze assessment (Sandeep decides)

| Field | Value |
|---|---|
| Automated checks on exact build `a70c40e` (Windows and LF checkout) | PASS |
| Browser runs on `a70c40e` | B, C, N1, N2 as expected; **A fails (vision)** |
| RELATIONSHIP_RECORD_APPROVED | NO |
| EVIDENCE_BACKED_ANSWER_VERIFIED | NO |
| APPLICATION_FREEZE_READY | **Recommendation: NO.** The committed build cannot read prescription images |

Remaining blockers:
1. **Image extraction:** it needs the vision schema remediation committed, with Sandeep's NVIDIA edits as one candidate, and then a rerun of scenario A on that commit.
2. **Still open:**
   - B-LIVE-NVIDIA-LLM-TIMEOUT: NVIDIA answered 1 of 3 calls today.
   - B-LIVE-DISCLAIMER-RESIDUE.
3. **REL-LIVE-0002:** approval is pending, and the evidence-backed answer is unverified.

## Clean-up for Sandeep

Remove the temporary worktrees when done:
- `acf08ee-fullsuite-wt`, `-wt2`, `-wt3`
- `freeze-verify-bafc083`
- `freeze-verify-a70c40e` and `freeze-verify-a70c40e-lf`
