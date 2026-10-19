# Risk tier and evidence eligibility fix: validation report

**Date:** 2026-10-14
**Branch:** `ui/3d-redesign`, code commit `82c128f` (fast-forward from `2d37ed1`, no force push, no PR)
**Request:** the researcher's decisions of 2026-10-14 on risk classification (Decision B) and evidence eligibility (Decision C). Decision A (Additional Instructions) was approved with conditions and is unchanged here.

**Freeze status:** NOT READY. See section 7 for the follow-up of the same day (`42f1676`) and what is still needed.

## 1. What changed

### Risk tier (Decision B)

The live application no longer classifies the bare drug names. `live_risk_tier()` in `src/adaptive_trust_medical_rag/services/live_relationships.py` decides the tier:

| Input | Tier | Basis shown to the user |
|---|---|---|
| Two or more medications, no approved severe record | R2 (threshold 0.60) | "a multi-drug interaction question with no approved severe relationship record" |
| Two or more medications, an approved CONTRAINDICATED or MAJOR record linking two of them | R3 (threshold 0.75) | "approved relationship record REL-…: A and B contraindicated (source CHUNK-ID)" |
| One medication | keyword classifier on the name (unchanged `classify_query_risk`) | "keyword classification of the medication name" |

- The multi-drug case passes the question "drug interaction between A and B" through the existing `classify_query_risk`, which returns R2. That matches `reports/audit/risk_tier_resolution.md`, where drug-drug interactions are R2 and contraindications R3. **This R2 default is a choice made for this fix and needs the researcher's confirmation.**
- R3 comes only from an approved relationship record. It never comes from the names, an LLM severity label, a retrieval score or an NLI score. A record can only raise a tier.
- When approved records disagree (one severe, one NONE), the higher tier is kept and the basis says so.
- No second classifier was added. The thresholds are the existing `config/trust.yaml` values (R0 0.30, R1 0.45, R2 0.60, R3 0.75); `TRUST_THRESHOLDS` in `live_application.py` is checked against that file by a test.

### Relationship records

- New loader: `src/adaptive_trust_medical_rag/services/live_relationships.py`.
- New versioned candidate dataset: `data/live_medical/relationships/LIVE_RELATIONSHIP_RECORDS_V1.json` (sha256 `b4d06362e2d21edbf43826ec7aa79a3282946a025521a50ee6d41d5b9314d277`) with `LIVE_RELATIONSHIP_RECORDS_V1_MANIFEST.json`.
- The loader reads records only when the manifest's status is `APPROVED`, it names `approval.approved_by` and `approval.approved_at`, and `records_sha256` matches the records file (CRLF normalised to LF). Anything else loads no records.
- Each record must have:
  - two resolved RxCUIs that are different;
  - a predicate from the existing bounded set in `canonical_identity.py`;
  - a known direction;
  - a severity in CONTRAINDICATED, MAJOR, MODERATE, MINOR or NONE;
  - a source chunk that exists in `LIVE_MEDICAL_CORPUS_V2` and whose content hash matches;
  - a verbatim evidence span that names both medications.
  Invalid records are rejected with a logged reason.
- The one candidate record, REL-LIVE-0001, is simvastatin (RxCUI 36567) CONTRAINDICATION clarithromycin (RxCUI 21212), A_TO_B, CONTRAINDICATED, from `DAILYMED-SPL-SIMVASTATIN-001-CHUNK-01`.
  - Its status is `CANDIDATE_PENDING_RESEARCHER_APPROVAL` and it was prepared by Claude, not by a reviewer.
  - The manifest lists what to check before approval: the source URL is a placeholder, the RxCUIs were not checked against RxNav from this environment, and the predicate, severity and direction need confirmation.
  - **The running application therefore loads no records, and the pair is classified R2, not R3, until the researcher approves it.**
- The frozen corpus is untouched. `LIVE_MEDICAL_CORPUS_V2.json` (blob `8cba1a45…`) and `LIVE_MEDICAL_CORPUS_MANIFEST_V2.json` (blob `dd8422db…`) are identical at `2d37ed1` and `82c128f`. The only data files added are the two above.

### Evidence eligibility (Decision C)

- The 0.5 entity-match fallback in the trust stage is removed.
- A chunk is eligible only if it names at least one requested medication by its canonical (RxNorm) name as a whole word (`aligned_medications()`). A chunk that names none is counted in `unrelated_excluded` and skipped before scoring. It reaches neither the trust score nor the LLM, and no retrieval or authority score can let it back in.
- When every safe chunk is unrelated, the analysis abstains before the LLM with: "N evidence chunk(s) passed security checks, but none names a requested medication (A, B), so none can support this analysis."
- The answer verifier enforces the same boundary.
  - A chunk carries a relationship identity only if exactly one approved record names that chunk, its current content hash and the requested pair, and no approved record for the pair says NONE.
  - `ClaimVerifierV2` itself is unchanged; it still requires a canonical identity MATCH for every claim. A pairwise claim with no identity, the wrong pair, the wrong relation or the wrong direction stays UNSUPPORTED, and the answer abstains.
- The post-generation abstention now separates "the evidence records carry no relationship identity" from "did not match an approved relationship record (a different drug pair, relation or direction, or no drug pair named)".

### Frontend

- `frontend/src/types/index.ts`: `TrustInfo` gains `risk_basis` and `unrelated_excluded`.
- `frontend/src/components/results/TrustSummary.tsx`: shows "Risk tier basis: …" and "N retrieved chunk(s) named none of these medications and were excluded."
- `frontend/src/hooks/useAnalysis.ts`: an abstention keeps the trust details from earlier in the stream.
- `frontend/src/pages/WorkspacePage.test.tsx`: one new test.

### Files changed in `82c128f`

```
data/live_medical/relationships/LIVE_RELATIONSHIP_RECORDS_V1.json            (new)
data/live_medical/relationships/LIVE_RELATIONSHIP_RECORDS_V1_MANIFEST.json   (new)
src/adaptive_trust_medical_rag/services/live_relationships.py               (new)
src/adaptive_trust_medical_rag/services/live_application.py
tests/e2e/test_live_risk_and_eligibility.py                                 (new, 35 tests)
tests/e2e/test_live_failure_semantics.py                                    (one assertion reworded)
frontend/src/types/index.ts
frontend/src/components/results/TrustSummary.tsx
frontend/src/hooks/useAnalysis.ts
frontend/src/pages/WorkspacePage.test.tsx
```

## 2. Regression tests

`tests/e2e/test_live_risk_and_eligibility.py` runs the real `LiveApplicationPipeline` and the real `ClaimVerifierV2` on real `LIVE_MEDICAL_CORPUS_V2` chunk texts, with a stub retriever, an offline RxNorm normaliser and a counting LLM. Under `TESTING=1` the verifier's NLI is the repository's keyword mock, so these tests check the gates, not the NLI model.

| Area | Tests |
|---|---|
| Known contraindicated pair | approved record gives R3 at 0.75; names alone give R2; an LLM severity label does not raise the tier |
| Ordinary and unknown queries | a single drug stays R0; an unknown pair is R2; a MODERATE record stays R2 |
| R3 threshold | R3 uses 0.75 and `TRUST_THRESHOLDS` equals `config/trust.yaml`; an authority-0.45 chunk eligible at R2 is ineligible at R3 |
| Dataset approval | a candidate loads nothing; approval needs a named person and date; a hash mismatch loads nothing; a CRLF copy hashes the same; 8 kinds of ungrounded or incomplete record are rejected; the shipped candidate is valid but not loaded |
| Unrelated chunks | carbamazepine, aspirin and warfarin chunks with authority 0.95 cannot pass eligibility (abstain before the LLM, 0 LLM calls, `unrelated_excluded` 3, trust 0.0); adding them to a simvastatin chunk leaves the trust score equal to the simvastatin-only score; a chunk naming one requested drug stays eligible; atorvastatin is not a match for simvastatin |
| Pairwise claims | a supported pairwise record lets a matching claim through; missing identity abstains even at high entailment; a record for another pair gives no identity; a claim about a different pair is not supported; another relation is a MISMATCH; contradictory records give no identity; contradicting evidence blocks a claim the record matches; a record is not attached once the chunk text changes |
| Frozen data | the corpus file hash is unchanged |

## 3. Commands and results

All commands ran in the cloud worktree on the `82c128f` tree, Python 3.12 venv, `TESTING=1`.

| Check | Command | Result |
|---|---|---|
| Focused tests | `TESTING=1 PYTHONPATH=src python -m pytest -q -p no:cacheprovider tests/e2e/test_live_risk_and_eligibility.py tests/e2e/test_live_failure_semantics.py` | 60 passed |
| Backend suite | `TESTING=1 PYTHONPATH=src python -m pytest -q -p no:cacheprovider -o log_cli=false` | 1302 passed, 4 skipped |
| Frontend tests | `npx vitest run` (in `frontend/`) | 88 passed |
| Frontend build and type check | `npm run -s build` | passed |
| Frontend lint | `npm run -s lint` | 0 errors, the 3 existing warnings |
| Ruff | `ruff check src/ tests/ .agents/scripts/` | All checks passed |
| Bandit | `python .agents/scripts/ci/run_bandit.py` | no medium or high severity issues |
| Whitespace | `git diff --check 2d37ed1..82c128f` | clean |
| Secret scan | added lines of `git diff 2d37ed1..82c128f` through `.agents/scripts/pre_commit_secret_scan.py` | nothing found |
| Protected artifacts | `python scripts/verify_v3_1_integrity.py`; `python scripts/verify_v3_confirmed_separation.py` | PASS, PASS |
| Frozen live corpus | `git rev-parse 2d37ed1:<file> 82c128f:<file>` for the V2 corpus and manifest | identical |

The backend suite rewrites `experiments/runs/live-smoke-v1/*` and some `reports/audit/*.md`; those were restored with `git checkout -- experiments reports` before committing, so no generated evidence is in the commit.

## 4. Browser runs (cloud, stand-ins)

Same harness as the cloud scenario report of 2026-10-14 (kept outside the repository, with its screenshots and captures): real frontend and backend, fixture vision, RxNorm and LLM, and the TESTING zero-vector embedding stub (`embedding_mode: "testing_stub"`). **These are not real retrieval and not a live verification.**

| Run | Tier | Threshold | Unrelated excluded | Outcome |
|---|---|---|---|---|
| A, B and C on `82c128f` with the shipped (unapproved) candidate | R2 | 0.60 | 7 of 8 | abstained: "3 of 3 generated claims failed post-generation verification. 3 of them could not be matched to a drug relationship because the evidence records carry no relationship identity." |
| B with a test-only approved copy of the candidate (`approved_by: "cloud test only (not a reviewer)"`, outside the repository) | R3 | 0.75 | 7 of 8 | abstained: "3 of 3 generated claims failed post-generation verification. 2 of them did not match an approved relationship record…" |

In both runs only the simvastatin chunk reached the LLM, and the Trust panel showed the tier basis and the excluded count.

In the R3 run the three fixture claims failed for these reasons:
- Claim 1 ("Simvastatin with clarithromycin is contraindicated… [Source 1]. This is a research output, not clinical advice.") matched the record's identity but was UNSUPPORTED. From reading the code, the verifier splits the statement and the disclaimer sentence names no drug pair, so it has no identity. This explanation is inferred from code, not traced at runtime.
- Claim 2 ("Simvastatin interacts with Clarithromycin…") was a MISMATCH: the predicate is INTERACTION and the record's is CONTRAINDICATION.
- Claim 3 ("Clarithromycin with simvastatin increases the risk…") was a MISMATCH: the subject order is reversed.

`ClaimVerifierV2` is shared with the research pipeline and was not changed.

## 5. Remaining limitations

1. **R3 is not active.** REL-LIVE-0001 is a candidate. Until the researcher verifies and approves it, the pair runs at R2.
2. **The source URL is a placeholder.** `LIVE_MEDICAL_CORPUS_V2` uses placeholder DailyMed URLs, and the RxCUIs were not checked against RxNav (blocked from this environment).
3. **Entity alignment is a whole-word match on the canonical name.** The corpus has no per-chunk RxCUI metadata, so brand names, salts or misspellings in chunk text are not matched. A chunk that names a drug only by brand is treated as unrelated, which fails closed.
4. **The verifier's identity check is exact and applies to every claim.** Disclaimers, single-drug statements, reversed subject order and INTERACTION-versus-CONTRAINDICATION wording all fail it. With the current verifier an answer abstains even with an approved record. Whether that check should apply to claims that name no relationship is an open researcher decision (blocker B-CLAIM-EVIDENCE).
5. **No real embedding retrieval or live providers ran here.** MiniLM, RxNav, DailyMed, openFDA and the LLM providers are not reachable from the cloud environment. `REAL_EMBEDDING_RETRIEVAL_VERIFIED` and `EVIDENCE_BACKED_ANSWER_VERIFIED` remain not verified.
6. **No mechanism-claim category exists**, so a mechanism statement is checked against the same pairwise identity.

## 6. What is still needed before the application freeze

- The researcher reruns scenarios A, B and C locally with the real embedding model and confirms:
  - `embedding_mode: "real"` in the `retrieval` event;
  - the tier and basis in the Trust panel (R2 before approval, R3 after);
  - unrelated chunks counted as excluded;
  - a terminal state for each run.
- The researcher verifies and approves, amends or rejects REL-LIVE-0001.
- The browser results of that run are retained.
- The open BASELINE decision for Free Replication V1 is unchanged.

## 7. Follow-up, 2026-10-14: researcher decisions and verifier wording (`42f1676`)

### Decisions recorded

- **R2 default confirmed by the researcher.** A multi-drug query with no approved severe record is R2 (0.60). This is the policy fallback and does not mean the combination is safe or low risk.
- **REL-LIVE-0001: verify first.** The record is not approved, and approval needs the researcher's explicit decision.

### Working copy at the start (Phase 1)

- The researcher's working copy was on `ui/3d-redesign` at `7a73f21`, matching `origin/ui/3d-redesign`. The remote is `https://github.com/sandysunny99/adaptive-trust-medical-rag.git`. `git worktree list` shows seven Copilot worktrees, all marked prunable.
- It had 14 modified tracked files, which were preserved:
  - `.env.example` (content not read);
  - `experiments/runs/live-smoke-v1/` `case_results.jsonl`, `manifest.json` and `summary.json`;
  - `reports/audit/` `ablation_runtime_integrity_smoke.md`, `canonical_r1_verification.md`, `five_case_validation.md` and `live_smoke_integrity.md`;
  - `src/adaptive_trust_medical_rag/api/app.py`;
  - `src/adaptive_trust_medical_rag/llm_backend/` `model_registry.py` and `openai_vision_backend.py`;
  - `tests/providers/test_vision_backend.py`;
  - `track_a_annotation/qa/` `TRACK_A_ANNOTATION_QA_V1.json` and `TRACK_A_ANNOTATION_QA_V1.md`.
- The listed redesign changes are present in that tree because they are in its commits:
  - confirmation objects and the 422 tests (`ae56f38`, `237f34e`);
  - retrieval errors and the answer gate (`8dca217`);
  - error-stage display (`988203a`, `2d37ed1`);
  - Additional Instructions screening (`6b97907`);
  - patient context (`ecb7fb9`);
  - the R2/R3 tier, unrelated-chunk exclusion and the Trust panel fields (`82c128f`).

### Source verification

The DailyMed and RxNav results are reported in `REL_LIVE_0001_SOURCE_VERIFICATION_2026-10-14.md`.
- **RxCUIs.** 36567 is simvastatin and 21212 is clarithromycin; both are ingredient (IN) concepts.
- **Sources.** Both labels support a contraindication of taking the two drugs together: ZOCOR section 4 and Table 2, and clarithromycin section 4.5.
- **Provenance.** The frozen chunk is not verbatim label text and has a placeholder URL. REL-LIVE-0001 therefore fails two provenance checks and stays pending.
- **Next.** A V2 candidate needs byte-exact label text, which `scripts/capture_live_relationship_sources.py` captures on a machine that can reach DailyMed.

### Verifier wording (Phase 6)

`ClaimVerifierV2` and `canonical_identity.py` are unchanged. Research integrity records assert `canonical_identity_unchanged`, so the changes are in the live layer only.

| Case | Change | Still fails closed when |
|---|---|---|
| A model-written research disclaimer in the conclusion | The sentence is removed from the conclusion, neither verified nor released, and listed in `removed_disclaimers`. The app shows its own fixed disclaimer. A sentence counts only if every word is in a fixed non-clinical vocabulary and it uses a disclaimer term | The sentence has a drug name, an effect, an instruction, a number or a `[Source N]` reference. It then stays in the conclusion and is verified. A conclusion that is only a disclaimer leaves nothing to release |
| "interacts with" against a CONTRAINDICATION record | An interaction item whose own severity or type label says contraindicated (without negation) is stated "A is contraindicated with B", so it is checked as a contraindication. The label only decides what is claimed | Any "interacts with" claim against a CONTRAINDICATION record is a predicate MISMATCH. The two are never treated as equivalent |
| Reversed drug order | A record may be BIDIRECTIONAL only for a symmetric predicate (CONTRAINDICATION, INTERACTION). For such a record the identity is given in the claim's drug order | A directional record (A_TO_B or B_TO_A) is never reoriented. A different pair or a different predicate is a MISMATCH. A BIDIRECTIONAL record with a directional predicate is rejected at load |

For the three claims of the cloud R3 run:
- the disclaimer no longer blocks claim 1;
- claim 2 matches only if the interaction item labels the combination contraindicated;
- claim 3 ("Clarithromycin with simvastatin increases the risk…") still fails, because its predicate is INCREASES, not CONTRAINDICATION.

That last result is the intended strict outcome. With no approved record, every pairwise claim still has no identity and the answer abstains.

New tests:
- 24 in `tests/e2e/test_live_risk_and_eligibility.py`: disclaimer removal and smuggling attempts, statement wording, the predicate kept exact, symmetric versus directional records, record validation, and abstention without an approved record;
- 3 in `tests/test_capture_live_relationship_sources.py`.

### Commands and results on `42f1676`

| Check | Command | Result |
|---|---|---|
| Live risk, eligibility and wording tests | `TESTING=1 PYTHONPATH=src python -m pytest -q -p no:cacheprovider tests/e2e/test_live_risk_and_eligibility.py` | 59 passed |
| Identity, verifier, failure semantics, Additional Instructions, capture | `… tests/test_capture_live_relationship_sources.py tests/test_canonical_identity.py tests/test_claim_verifier_v2.py tests/e2e/test_live_failure_semantics.py tests/e2e/test_additional_instructions.py` | 113 passed |
| Backend suite | `TESTING=1 PYTHONPATH=src python -m pytest -q -p no:cacheprovider -o log_cli=false` | 1329 passed, 4 skipped |
| Frontend | `npx vitest run`; `npm run -s build`; `npm run -s lint` | 88 passed; build passed; 0 errors, the 3 existing warnings |
| Ruff | `ruff check src/ tests/ .agents/scripts/ scripts/capture_live_relationship_sources.py` | All checks passed |
| Bandit | `python .agents/scripts/ci/run_bandit.py` | no medium or high severity issues |
| Whitespace and secrets | `git diff --check`; added lines through `pre_commit_secret_scan.py` | clean; nothing found |
| Protected artifacts | `scripts/verify_v3_1_integrity.py`; `scripts/verify_v3_confirmed_separation.py` | PASS, PASS |
| Frozen files | `git diff 7a73f21 42f1676` on the V2 corpus and manifest, `verification/` and `prompts/` | unchanged |

The suite-rewritten `experiments/runs/live-smoke-v1/*` and `reports/audit/*.md` files were restored before committing.

### Status after the follow-up

| Status | Result | Evidence |
|---|---|---|
| CONFIRMATION_CONTRACT_FIXED | Verified | Regression tests and the cloud browser run (`/confirm` 200). Local confirmation is part of the researcher's run |
| REAL_EMBEDDING_RETRIEVAL_VERIFIED | Not verified | MiniLM cannot be downloaded in the cloud, and reading the researcher's local model cache was not permitted from this session. Needs the local run with `embedding_mode: "real"` |
| RELATIONSHIP_RECORD_VERIFIED_PENDING_APPROVAL | Not yet | REL-LIVE-0001 failed two provenance checks; the V2 candidate waits on the byte-exact capture |
| RELATIONSHIP_RECORD_APPROVED | No | Needs the researcher's explicit decision on a verified candidate |
| EVIDENCE_BACKED_ANSWER_VERIFIED | No | No approved record and no local run |
| CONTROLLED_ABSTENTION_VERIFIED | Verified with stand-ins | Cloud runs and tests; the local run is still to come |
| APPLICATION_FREEZE_READY | No | Waits on the local A, B and C runs with retained results, and on a decision about a verified relationship candidate |

### Local runs: what to record for each of A, B and C

- branch, commit and build;
- input mode, whether NVIDIA vision was called, and whether RxNorm was live;
- `embedding_mode` and `embedding_model`, the retrieval count and the eligible count;
- the risk tier and its basis, and `unrelated_excluded`;
- each claim's relationship identity result and support state, and `removed_disclaimers`;
- the terminal `answer`, `abstention` or error;
- sanitised screenshots and the saved event stream.
