# Vision fence tests and the full browser set on the committed source, 2026-10-18 (evening)

This covers Sandeep's "continue" at 16:39 and 16:45 UTC, taken as option "Both". Evidence: `followup_2026-10-18c/`. No existing run file was overwritten.
- Not done: no push, tag, reset, stash, amend or branch change.
- Untouched: REL-LIVE-0002 is still pending, `data/live_medical/relationships/` is untouched, and the freeze is not declared.
- After the interruption, HEAD was still `a0321d8` and the test file was clean, so nothing partial needed handling.

## Commit `9bae325` (local, test-only)

test(vision): reject invalid content inside a code fence.

- **What it adds:** `tests/providers/test_vision_backend.py` +26. One test, `test_30_invalid_content_inside_code_fence_rejected`, covers 7 replies that must each raise SCHEMA_ERROR:
  - malformed JSON in a fence;
  - prose in a fence;
  - nested fences;
  - three schema-invalid objects in a fence (missing `candidate_medications`, `candidate_medications` not a list, empty candidate `raw_text`);
  - an unclosed fence.
- **No source change:** `git diff a0321d8 9bae325 -- src` is empty. The committed parser already rejected every case.
- **Checks:** staged by exact path, gitleaks found no leaks in the staged change, the pre-commit scan passed, ruff is clean, and the vision tests gave 30 passed.

## Exact build `9bae325`

Fresh worktree `C:\Users\sunny\freeze-verify-9bae325`, with nothing uncommitted.

| Check | Result |
|---|---|
| Vision tests | 30 passed |
| Full backend suite | **1470 passed, 4 skipped, 0 failed** (exit 0, 396 s) |
| 7 historical files, sha256 before vs after | identical |
| `git status` before, after and after checks | clean |
| ruff | clean |
| `run_bandit.py` | exit 0 |
| Integrity scripts | PASS, PASS |
| `audit_frozen_hash_line_endings.py --check` | 311 CRLF-recorded, 0 unpinned |
| gitleaks over `a0321d8..9bae325` | no leaks |

## Browser runs on `9bae325` (source identical to `a0321d8`)

**Setup**
- The backend ran on 127.0.0.1:8010 from the worktree; the launcher logged "exact-build code: C:/Users/sunny/freeze-verify-9bae325/src/...".
- Credentials were loaded from the repo's `.env.local` and `.env` into the backend process only. Nothing was printed, logged or copied.
- The frontend ran on 127.0.0.1:5180 from the worktree, with a temporary config and a junction, both removed afterwards. Sandeep's 8000 and 5173 were not used.
- About 1 GB of memory was free; no resource problems.
- Scenario A was not rerun. It passed on `a0321d8`, which has the same source (`ADDENDUM_NVIDIA_COMMIT_2026-10-18.md`).

| Run | Selection | Answered by (stream `served_by`) | Embedding | Retrieved / eligible / unrelated | Tier | Result |
|---|---|---|---|---|---|---|
| B-direct-cloudflare | manual cloudflare | cloudflare / @cf/meta/llama-3.3-70b-instruct-fp8-fast, stop, 1702 chars | real (all-MiniLM-L6-v2) | 14 / 1 / 13 | R2 0.60 | abstention, 8 of 8 claims withheld |
| B-direct-nvidia | manual nvidia | nvidia / nvidia/nemotron-3-super-120b-a12b, stop, 1211 chars | real | 14 / 1 / 13 | R2 0.60 | abstention, 5 of 5 withheld |
| C-context | auto | groq / openai/gpt-oss-120b, stop, 1513 chars (NVIDIA timed out first) | real | 14 / 1 / 13 | R2 0.60 | abstention, 5 of 5 withheld |
| N1-note-policy | auto | groq / openai/gpt-oss-120b, stop, 1599 chars (NVIDIA timed out first) | real | 14 / 1 / 13 | R2 0.60 | abstention, 6 of 6 withheld |
| N2-note-injection | auto | none | n/a | n/a | n/a | INPUT_REJECTED (log: marker name and length only) |

- **Retrieval:** `relationship_evidence_chunks` is `[]` everywhere, so REL-LIVE-0002 is not loaded.
- **Credentials:** none found in the evidence (kit scan and gitleaks).
- **Coverage:** with A on `a0321d8`, every browser scenario (A, B-CF, B-NV, C, N1, N2) has now run on the committed source.

## Freeze assessment (Sandeep decides)

| Field | Value |
|---|---|
| Automated checks on exact build `9bae325` | PASS |
| Browser scenarios on the committed source (`a0321d8` = `9bae325` source) | all as expected: image read and confirmed (A), R2 abstentions with real retrieval (A, B-CF, B-NV, C, N1), injection rejected (N2) |
| CONFIRMATION_CONTRACT_FIXED / REAL_EMBEDDING_RETRIEVAL_VERIFIED / CONTROLLED_ABSTENTION_VERIFIED | YES / YES / YES |
| Image extraction on a committed revision | YES (synthetic scope) |
| RELATIONSHIP_RECORD_APPROVED | NO |
| EVIDENCE_BACKED_ANSWER_VERIFIED | NO |
| APPLICATION_FREEZE_READY | not declared; Sandeep's call |

Remaining:
1. **B-LIVE-NVIDIA-LLM-TIMEOUT:** open. NVIDIA timed out 4 of 4 times in auto mode today and answered every time it was selected directly. The 30 s timeout and the NVIDIA-first auto order are unchanged.
2. **B-LIVE-DISCLAIMER-RESIDUE:** open. Those claims are withheld.
3. **REL-LIVE-0002:** approval pending. The evidence-backed answer is unverified.
4. **Push:** pending Sandeep's decision.

## Clean-up for Sandeep

Remove the temporary worktrees when done:
- `acf08ee-fullsuite-wt`, `-wt2`, `-wt3`
- `freeze-verify-bafc083`
- `freeze-verify-a70c40e`, `freeze-verify-a70c40e-lf`
- `freeze-verify-a0321d8`, `freeze-verify-9bae325`
