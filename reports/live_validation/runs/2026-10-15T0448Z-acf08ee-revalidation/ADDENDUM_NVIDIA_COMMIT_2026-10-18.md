# NVIDIA commit and scenario A on the committed build, 2026-10-18

This covers Sandeep's 10:45:57 UTC instruction (option A). Evidence: `followup_2026-10-18b/`. No existing run file was overwritten.
- Not done: no push, tag, reset, stash, amend or branch change.
- Untouched: REL-LIVE-0002 is still pending, `data/live_medical/relationships/` is untouched, and the freeze is not declared.

## Commit `a0321d8` (local)

feat(nvidia): separate NVIDIA LLM and vision credentials; parse vision output strictly

| File | Change |
|---|---|
| `src/adaptive_trust_medical_rag/api/app.py` | +39 lines changed: NVIDIA LLM key/model/base URL and NVIDIA OCR/vision key/model/base URL from the environment, each falling back to `NVIDIA_API_KEY`; nothing hard-coded |
| `src/adaptive_trust_medical_rag/llm_backend/model_registry.py` | +14: the NVIDIA model counts as configured with `NVIDIA_LLM_API_KEY` or `NVIDIA_API_KEY` |
| `src/adaptive_trust_medical_rag/llm_backend/openai_vision_backend.py` | +313: the exact JSON schema in the prompt, `response_format: json_object`, strict parsing and schema validation, fail closed |
| `tests/providers/test_vision_backend.py` | +266: 15 new tests (15–29); test 5 tightened (a missing `candidate_medications` now fails with SCHEMA_ERROR instead of reading as zero) |
| **Total** | 4 files, +567/-65 |

**Review**
- Each file holds only NVIDIA changes; app.py's earlier max-tokens hunk was already in `2947976`.
- Staged with `git apply --cached` from a reviewed patch. Nothing else was staged.
- gitleaks found no leaks in the staged changes, the CI hook allowed 4 of 4, and the pre-commit gate passed.
- Ruff is clean, and Bandit on the 3 sources exits 0.
- Before committing: vision, model selector, image confirmation, failure semantics and confirmation contract gave **85 passed**.
- **Left out and still uncommitted, unchanged:** `.env.example` (not read), the 7 historical report and run files, both `TRACK_A_ANNOTATION_QA_V1` files, `track_a_annotation/ai_assisted/` and the register edit. The 4 committed files are byte-identical in Sandeep's working copy before and after.

## Vision checks on `a0321d8` (fresh worktree, nothing uncommitted)

- **Committed vision tests:** 29 passed. Coverage:
  - malformed JSON: test 4;
  - valid fenced JSON: test 15;
  - schema-invalid replies: tests 5, 24, 25, 26, 29;
  - other: prose (17, 22), trailing text after a fence (23), empty reply (18), the bullet fallback (16), confidence mapping (19, 27), `response_format` (21), injection text (20).
- **Gap in the committed tests:** none covers malformed JSON inside a fence, non-JSON inside a fence, nested fences, schema-invalid JSON inside a fence, or an unclosed fence.
- **Throwaway check, not committed** (`throwaway_vision_fence_checks.py.txt`, run with the worktree's `src`): **17 passed.**
  - All 7 bad shapes raise SCHEMA_ERROR, both from the parser and through `extract_medications`.
  - Plain, ```` ```json ```` and bare ```` ``` ```` fenced valid replies parse into the schema.
  - The behaviour is correct; only test coverage is missing. No test was added to the repo.

## Browser scenario A on `a0321d8`

**Setup**
- The backend ran on 127.0.0.1:8010 from the worktree's code; the launcher logged "exact-build code: C:/Users/sunny/freeze-verify-a0321d8/src/...".
- Credentials: loaded from the repo's `.env.local` and `.env` into the backend process only, as this morning. Nothing was printed, logged or copied.
- The frontend ran on 127.0.0.1:5180 from the worktree, with a temporary config and a `node_modules` junction, both removed afterwards.
- Sandeep's 8000 and 5173 were not used. Port 8000 is held by Docker.
- Image: `synthetic_rx.png`, sha256 `aad8f522…2f38`.

**Result** (one run, `stream_complete: true`, 24 events in the page and 24 over the network)

| Stage | Result |
|---|---|
| Vision | nvidia_vision / meta/llama-3.2-11b-vision-instruct. Candidates: Simvastatin (normalized Simvastatin, HIGH) and Clarithromycin (normalized Clarithromycin, HIGH). Warnings `[]`, so this was schema JSON and the bullet fallback was not used |
| Confirmation | `/confirm` 200; body = medication objects with status CONFIRMED, source VISION |
| RxNorm | 36567 simvastatin and 21212 clarithromycin, `rxnorm_source` rxnorm_exact, MATCHED |
| Retrieval | `embedding_mode: "real"` (all-MiniLM-L6-v2); 14 retrieved, 1 eligible, 13 unrelated excluded; `relationship_evidence_chunks: []` |
| Trust | R2, threshold 0.60, trust 0.935, basis "a multi-drug interaction question with no approved severe relationship record" |
| Answering model | `served_by`: nvidia / nvidia/nemotron-3-super-120b-a12b (reported the same), finish `stop`, 1202 chars. No failover or provider failure in the backend log |
| Terminal | abstention: 6 of 6 claims withheld, no relationship identity (REL-LIVE-0002 not loaded) |

No credential-shaped strings were found in the browser evidence (kit scan and gitleaks).

## Full verification on `a0321d8`

| Check | Result |
|---|---|
| Full backend suite | **1469 passed, 4 skipped, 0 failed** (exit 0, 440 s) |
| 7 historical files, sha256 before vs after | identical |
| Worktree `git status` before, after and after checks | clean |
| ruff `src/ tests/` + audit script | clean |
| `run_bandit.py` | exit 0 |
| Integrity scripts | PASS, PASS |
| `audit_frozen_hash_line_endings.py --check` | 311 CRLF-recorded, 0 unpinned |
| Hook allow/deny | OK, OK |
| gitleaks over `a70c40e..a0321d8` | no leaks |
| Sandeep's working-copy 7 files | unchanged |
| `data/`, prompts, `verification/`, `trust_scoring/` since `c490393` | unchanged |

## Freeze assessment (Sandeep decides)

On the exact committed build `a0321d8`, every automated check passed, and scenario A now runs end to end. B, C, N1 and N2 ran on `a70c40e`, which has the same code except the NVIDIA commit; they were not rerun on `a0321d8`.

| Field | Value |
|---|---|
| CONFIRMATION_CONTRACT_FIXED | YES (A on `a0321d8`) |
| REAL_EMBEDDING_RETRIEVAL_VERIFIED | YES |
| CONTROLLED_ABSTENTION_VERIFIED | YES |
| Image extraction on a committed revision | YES (synthetic scope) |
| RELATIONSHIP_RECORD_APPROVED | NO |
| EVIDENCE_BACKED_ANSWER_VERIFIED | NO |
| APPLICATION_FREEZE_READY | not declared; Sandeep's call |

Remaining:
1. **B/C/N1/N2 on `a0321d8`:** not rerun. The NVIDIA commit changes NVIDIA provider registration, so a rerun would make the browser set fully exact-build.
2. **NVIDIA LLM timeouts:** still open, 2 successes in 4 calls today.
3. **Disclaimer residue:** still open.
4. **Vision test coverage:** fenced-invalid shapes are not in the committed tests. The behaviour is verified by the throwaway check only.
5. **REL-LIVE-0002:** approval pending.
6. **Push:** pending Sandeep's decision.

## Clean-up for Sandeep

Remove the temporary worktrees when done:
- `acf08ee-fullsuite-wt`, `-wt2`, `-wt3`
- `freeze-verify-bafc083`
- `freeze-verify-a70c40e`, `freeze-verify-a70c40e-lf`
- `freeze-verify-a0321d8`
