# Medical RAG round 7, candidate C1: four curated-cache corrections (2026-10-27)

Research prototype. Software tests do not establish clinical correctness, patient safety, regulatory compliance or production readiness. C1 was approved alone. C2, M1 and C3 have not started.

## Verdicts, kept separate

| Category | Status |
|---|---|
| Engineering validation of C1 | **Pass.** Every check below was run on the integrated C1 candidate and passed. |
| Medication-identity coverage | **BLOCKED.** P07 (metamizole) and P08 ("Zorbitrex") are still released as verified. The residual test is still a strict xfail. C1 does not change this. |
| Evidence-support verification | Unchanged. |
| Research readiness | Not ready (C2 and M1 outstanding). |
| Clinical validation | None. |

## 1. Isolated candidate

- **Path:** `C:\Users\sunny\r7-c1-cache`. Made with `git clone --local --no-checkout` of the Round-6 repository, then `git checkout --detach 2190fb0`. The clone's `origin` remote was removed so nothing can be pushed from it.
- **HEAD:** `2190fb047f1808de2e6a093305db125d2c8a8758` (detached). Clean right after checkout (0 status lines).
- **Round-6 candidate:** the 24 files were copied from the preserved `C:\Users\sunny\round6-evidence-2026-10-27\candidate_tree\` (its `SHA256SUMS.txt` verified first), not from the live checkout.
- **Fingerprint:** `sha256sum -c r6c_fingerprint.txt` gave **24 OK, 0 failed**, before any C1 change.
- **Discrepancy noted (not a fingerprint difference):** 964 other tracked files differ from the Round-6 checkout **only in line endings**. The clone checks out CRLF (`core.autocrlf=true`); the checkout has LF. With CR removed, content is identical for all 964. Files pinned by `.gitattributes` are unaffected, and the frozen line-ending audit passes.
- **Environment:** `uv sync --frozen --offline` gave the same 144 packages as the Round-6 checkout. `npm ci --prefer-offline` installed 141 packages. No `.env` or `.env.local` was copied, opened or created.

## 2. C1 diff

- **Patch:** `cache-fix-b3a3d3e.INTEGRATION.patch`, SHA-256 `49d89c5a817c3d1dda36340aa64fa5f3db2d9fc08c93aecc82a48c2449dccbba`, matching the recorded hash. Reviewed in full, `git apply --check` passed, then applied with `git apply`. Nothing staged or committed.
- **Changed by C1 (2 files, +45/−5):**
  - `data/drug_entity_cache.json`, 4 values only:

    | Key | Before | After |
    |---|---|---|
    | methotrexate | 7052 | 6851 |
    | metoprolol succinate | 866508 | 221124 |
    | metoprolol tartrate | 866514 | 203191 |
    | lopressor | 866514 | 203191 |

  - `tests/test_drug_normalizer.py`: a 4-case parametrised test pins each mapping, read through the cache by `DrugNormalizer` (`source == "cache"`, RxCUI and generic name). Another test rejects the retired values 7052, 866508 and 866514 under the four keys and under every key in the file.
- **Cache check (scripted):** 26 entries, keys and key order identical; the same field set in every changed entry; only `rxcui` changed in those 4; **22 entries byte-identical**. Schema and ingredient-level convention unchanged (Lopressor keeps its generic's RxCUI).
- **Exact candidate diff** (tracked files, `git diff` of the 2 C1 files): `C:\Users\sunny\r7-c1-cache.C1.diff`, SHA-256 `76155e86be760ada17c2d9414d45b4d3d3609d85122ed52059f838d4caed57d0`.
- **New candidate artifact:** `experiments/nli_eval_round6/results/LEXICON_COVERAGE_C1_CANDIDATE.json` (SHA-256 `9bdf87d4…f8ee`), produced by the unmodified coverage script with only its output path redirected. The frozen `LEXICON_COVERAGE_V1.json` is unchanged (`401c7c3f…33ab`). The difference: `same_rxcui_as_cache` 12 → 15 (methotrexate and both metoprolol salts now equal the lexicon). Lopressor still differs from the lexicon's brand concept 203344, by the cache's brand-to-generic convention. All other sections are identical.

## 3. Results (C1 candidate; logs in `C:\Users\sunny\r7-c1-logs\`)

| Check | Command | Result |
|---|---|---|
| Focused | `TESTING=1 uv run --offline pytest -q -p no:cacheprovider -o log_cli=false -rfsxX tests/test_drug_normalizer.py tests/test_medication_identity_guard.py tests/test_medication_lexicon.py tests/test_medication_lexicon_inventory.py tests/e2e/test_citation_alignment.py` | **119 passed, 1 xfailed** (metamizole, BLOCKING), exit 0. The 5 new C1 tests: 5 passed. |
| Backend, normal network | `TESTING=1 uv run pytest -q -p no:cacheprovider -o log_cli=false -rfsxX tests` | **1908 passed, 4 skipped, 1 xfailed**, exit 0 (11:50:46–11:55:54) |
| Backend, network blocked | the same, with `HTTP(S)_PROXY` and `http(s)_proxy=http://127.0.0.1:9`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `uv run --offline` | **1908 passed, 4 skipped, 1 xfailed**, exit 0 (11:56:07–12:57:24) |
| vitest | `npx vitest run` | **145/145** (22 files), exit 0 |
| TypeScript | `npx tsc -b` | exit 0, no output |
| oxlint | `npx oxlint` | exit 0; the same 3 warnings in untouched files (`WorkspacePage.tsx` ×2, `HistoryPage.tsx`) |
| ruff | `ruff check` on the 13 changed Python files | all checks passed |
| bandit | `bandit -q -ll -r experiments/nli_eval_round6` plus the 3 changed source files and the build script | exit 0, no findings |
| Whitespace | `git diff --check` (tracked); `git diff --no-index --check` for each of the 18 untracked candidate files | clean |
| Secrets | gitleaks 8.30.1, `gitleaks dir --redact` | **no leaks**. Scope: copies of the **26 changed files only** (the 24 Round-6 files plus the 2 C1 files), not the whole repository. |
| Integrity | `verify_v3_1_integrity.py`, `verify_v3_confirmed_separation.py`, `audit_frozen_hash_line_endings.py --check` | PASS, PASS, 311 pinned / 0 unpinned |
| Frozen data | eval set; lexicon; `git diff 2190fb0` over the eval set, prompts, `data/live_medical`, `data/evidence`, trust scoring, the model registry and the candidate fixtures | eval set `bd23fe48…f4ff` matches its manifest; lexicon `bcf0d184…1789`, release 05-Oct-2026; protected paths: no diff |
| Approval manifests | V1, food_0001, rel_live_0003, rel_live_0004 | all `CANDIDATE_PENDING_RESEARCHER_APPROVAL`; REL-LIVE-0004 still `UNGRADED` |

**Test-count reconciliation.** Round 6 ran 1907 passed + 1 xfail (1908 collected). C1 adds 5 tests, so 1913 are expected; 1908 + 4 + 1 = 1913.

## 4. Discrepancies and skipped checks

- **4 skips, environment only:** `tests/test_provider_connectivity_preflight.py` loads `.env.local` from the project root. The clone has none (deliberately), so the GROQ, GEMINI, HF and Cloudflare credential checks skip. They passed in Round 6 because that checkout has its env files. This is not a C1 effect and was not worked around.
- **Network-blocked run took 61 minutes** (Round 6: about 9). The result is the same. The likely cause is connection attempts timing out against the blocked proxy; it was not investigated further.
- **Line endings** of 964 untouched tracked files (section 1).
- **Not run:** browser flows, vision injection, real-model replay. C1 changes only the curated cache and its tests, and the Round-6 probes use lisinopril, which C1 does not touch.

## 5. Final state

- **Clone:** HEAD `2190fb0` detached. 8 modified tracked files: the 6 Round-6 files, `data/drug_entity_cache.json` and `tests/test_drug_normalizer.py`. Untracked: the 18 Round-6 files and the new coverage file inside `experiments/nli_eval_round6/`. Gitignored setup only: `.venv`, `frontend/node_modules`. Nothing staged or committed.
- **Round-6 checkout:** untouched. HEAD `2190fb0`, the 24-file fingerprint all OK, `git status` identical to before, apart from this report and the round-7 design document.
- **Cache-fix worktree:** untouched. HEAD `b3a3d3e`, clean.
- Nothing pushed anywhere.

Stopped after C1. C2, M1 and C3 each need separate approval.
