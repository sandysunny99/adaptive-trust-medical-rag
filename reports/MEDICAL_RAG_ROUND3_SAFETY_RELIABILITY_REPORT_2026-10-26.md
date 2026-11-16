# Medical RAG round 3: safety, verification reliability and research integrity (2026-10-26)

Research prototype. No result here establishes clinical correctness, clinical safety, regulatory compliance or production readiness. No evidence was graded or approved.

Branch `wip/pre-threads-20261022-1440`. The round started at `5c42bbc`, matching the round-2 report, and ended at `794aa7c` with 6 local commits. Nothing was pushed.

Evidence labels: **[unit]** · **[int]** service-level with stubs · **[mock-provider]** scripted LLM or vision · **[real-NLI]** the pinned PubMedBERT-MNLI-MedNLI model on real label text · **[real-provider]** real Groq, Cloudflare, NVIDIA or RxNav · **[http]** real HTTP/SSE · **[browser]** real UI.

## 1. Starting state (Phase 0)

- Branch and HEAD were as reported.
- The working tree held only the 3 stale `experiments/runs/live-smoke-v1/*` files. They were left untouched, as were the untracked user files: bundles, `cognee_service/`, `claude-incoming/`, `track_a_annotation/ai_assisted/` and earlier reports.
- No servers were running.
- The frozen V1 corpus is `1fdb0be65a1a2cf3d2847bf68fd6c5198c046760d44b23672f37dd9d78ca5578`, matching the full hash recorded in the feature-finalization report.
- `.env` and `.env.local` were not opened in any form (the permission rules deny it, and the instructions forbid it). Provider facts came from the app's startup log, and test configuration came from process environment variables only.

## 2. Findings and fixes

| ID | Sev | Finding | Root cause | Fix / test | Commit |
|---|---|---|---|---|---|
| R3-01 | **P1** | An injected image line produced "CYANIDE 100 MG" as a normal HIGH/DETECTED candidate. | Transcriptions were never screened. | `services/vision_screening.py` screens each transcribed line and each candidate (injection markers and detector). Flagged candidates are shown as UNCERTAIN with `screening_flags`, and the panel shows a warning. It never deletes. 11 backend tests [unit][int], 2 vitest. | `ead038c` |
| R3-02 | **P1** | False acceptance in the **shipped** verifier: with one eligible chunk (label §7.1), "Thiazide diuretics should be stopped in all patients taking lisinopril [Source 1]" was SUPPORTED at 0.999 [real-NLI]. | The overstatement check ran only on sources with reviewed wording, and §7.1 has none. | `source_text_violation` bounds a statement by the cited text itself (action level, certainty, quantity, timing). It can only withhold. Tests: 7 strength and 1 live gate. | `3d07e7b` |
| R3-03 | — | A candidate fix for false withholdings, comparing only the entailing chunk's own neutral score and stripping `[Source N]` before NLI, was **implemented, tested with the real model and rejected before commit**. | It released "Lisinopril should be stopped immediately in all patients" (0.991 entailment) and "Lisinopril causes kidney failure in all patients" (0.568) as SUPPORTED [real-NLI]. | The conservative rule is pinned with these real scores. | `7a053e8` |
| R3-04 | P2 | `/health` reads "unhealthy" whenever no research database is configured, which the live application never uses. | One endpoint mixed research DB health with live readiness. | `/health/live` (liveness) and `/health/ready` (503 until retrieval, the verifier and an LLM are ready; lists what is missing). `/health` keeps its contract. 5 tests. | `1a84f98` |
| R3-05 | P3 | The app was built twice under `--factory`, so the startup log printed every provider line twice. | The module-level `app = create_app()` ran at import. | It is now built lazily through a module `__getattr__` (subprocess test). | `1a84f98` |
| R3-06 | — | Whether R3 is reachable without an evidence-quality grade. | — | Tests: the best R3 score is 0.72 without quality and population; with population measured, R3 needs every other factor at exactly 1.0. | `aec62e0` |

## 3. Claim-verification reliability (Phase 2)

**Root causes of the false withholdings, measured with the real NLI model on real label text:**

1. **The conservative neutral rule.** The verifier compares the best entailment with the highest neutral score of *any* chunk. "Lisinopril interacts with spironolactone, increasing risk of hyperkalemia" was entailed by §7.1 at 0.998 and withheld because §5.5 was neutral at 0.999.
2. **Citation markers inside the NLI hypothesis.** "… monitored periodically in patients receiving lisinopril" scores 1.0 entailment without the marker. With "[Source 2]." appended it drops to 0.49.
3. **An NLI false contradiction.** "Lisinopril attenuates potassium loss caused by thiazide-type diuretics" (verbatim in §7.1) is rated a 0.98 contradiction of §5.5, so the claim is AMBIGUOUS. This caused every withheld lisinopril-only run in round 3.

**Why causes 1 and 2 were not "fixed":** the same model gives false entailments (0.991, 0.568 above, and 0.999 in R3-02). Causes 1 and 2 are what currently hide some of those false entailments. Removing them traded false withholdings for false acceptances, which this project must not accept. The real remedy is a better or calibrated NLI model, which is a research decision.

**Real-provider observations after R3-02** (12 Groq runs, V2 prompt, test-approved lisinopril evidence in a scratch folder) [real-provider][http]:

| Question | Released | Withheld | Causes of withholding |
|---|---|---|---|
| lisinopril + spironolactone | 4/6 | 2/6 | Both correct: the model applied the label's general "diuretics" hypotension warning to spironolactone ("diuretics such as spironolactone"), which no approved pair record supports. |
| lisinopril alone | 2/6 | 4/6 | 4 × the AMBIGUOUS "attenuates potassium loss" (NLI false contradiction); 1 × "Excessive reduction of blood pressure when combined with diuretics" INSUFFICIENT (cause 1). |

The new strength bound withheld none of the statements these runs produced. **No false acceptance was observed** in the released runs; each released statement was compared with the label text by hand.

**Deterministic acceptance matrix**, existing and new tests with scripted providers:

| Case | Expected | Test |
|---|---|---|
| Supported single-drug claim | released | `test_fully_verified_answer_is_released_…` |
| Supported pair claim, approved record | released | `test_a_supported_pairwise_record_lets_a_matching_claim_through` |
| Correct claim with no citation | withheld | `test_statement_without_a_citation_is_not_released` (3 fields) |
| Citation to an unretrieved source | withheld | `test_source_that_is_not_a_retrieved_chunk_cannot_be_released` |
| Citation to the wrong section | withheld | `test_a_fetal_toxicity_section_cannot_support_a_hyperkalemia_claim` |
| Partial support | withheld | `test_partial_support_is_not_supported` |
| Contradiction | withheld | `test_contradicting_evidence_blocks_a_claim_the_record_matches` |
| Class warning applied to a specific drug or pair | withheld | `test_a_claim_about_a_different_pair_is_not_supported_by_the_record`; observed for real (above) |
| Mixed multi-sentence conclusion | per-sentence verdict | `test_each_conclusion_sentence_is_verified_on_its_own` |
| Overstated or certain wording, unreviewed source | withheld | `test_a_statement_more_certain_than_an_unreviewed_source_is_withheld` |
| NLI false entailment hidden by the neutral rule | withheld | `test_claim_verifier_conservative_neutral.py` |
| Drug identity mismatch | withheld | `test_a_claim_with_another_relation_does_not_match_the_record`, AUD-10 |

## 4. Trust score (Phase 3)

The formula, weights, thresholds and missing-factor policy are unchanged since LIVE_TRUST_FACTORS_V2 (`51fb6cc`). No hard-coded relevance or default has returned (code review, and `test_unmeasured_factors_are_missing_not_defaulted`). Eligibility uses the unrounded score (AUD-07). The score is a heuristic, not a probability.

**Evidence quality.** No record carries one, so R3 is unreachable in practice (section 2, R3-06). **Proposal for researcher review; nothing was implemented:**
- Add `evidence_quality` and `evidence_quality_basis` to the V2 evidence schema. They would be set at capture time by the record builder (`scripts/build_*_candidate.py`), from a documented table such as FDA SPL label section type or study design.
- Approval would come through the same manifest gate as other evidence fields.
- Validating the table needs an independent reviewer's grades on a sample, with agreement measured.
- Until then, missing stays missing.

**Open research decisions:** whether `consistency = 1 − poisoning` is acceptable (it is a proxy, not cross-source consensus), and whether raw MiniLM cosine (uncalibrated; 0.57 for the best real chunk) is an adequate relevance signal.

## 5. RxNorm and food (Phases 4–5)

Re-verified by the full suite. Salt and brand concepts keep their exact RxCUI, and the RxNorm ingredient is shown but not substituted (`b52f308`). Metoprolol tartrate ≠ succinate is still pinned. An RxNav outage gives `NORMALIZATION_SERVICE_UNAVAILABLE` and the card shows "RxNorm unreachable" (`f2dd09b`). All five food states are tested over the service and the UI (`d5cedd4`).

One thing to note: on an abstention, the per-claim list shows the failed statements' text, food statements included, each marked with its failed state and reason. That is deliberate for traceability, but it does display unverified text.

## 6. Prescription fields (Phase 6): proposal only

The extraction schema (`raw_text`, `normalized_text`, `confidence`) has no strength, form or frequency, and the confirmation contract sends only a name. Doing this safely means changing the vision prompt and schema, `MedicationCandidate`, the confirm contract, and the UI, with per-field confidence and "missing/uncertain" states. That is too broad for this round without a dosing-safety design. Nothing in the pipeline uses dose today, and no dosing advice is generated.

Proposed fields: `strength {value, unit, raw, confidence}`, `dose_form`, `frequency {raw, confidence}`. Each would be nullable and confirmed by the user, never defaulted, and excluded from retrieval and the prompt until a reviewed use exists. Tests would cover backward-compatible SSE for old clients.

## 7. Providers (Phase 8)

- **Real Cloudflare failover** [real-provider][http]: a process-level `GROQ_MODEL=audit-nonexistent-model-for-failover-test` (`.env` untouched) made Groq return 404 MODEL_NOT_FOUND, and the router failed over. Cloudflare (`@cf/meta/llama-3.3-70b-instruct-fp8-fast`) served the answer in 16.5 s, and it was verified and released. The next request skipped Groq (marked unusable). Text routing remains Groq → Cloudflare, with NVIDIA out.
- **Vision** (Groq-first default, re-checked [real-provider]): the injected image's "CYANIDE 100 MG" was flagged `FROM_INSTRUCTION_LIKE_LINE`/UNCERTAIN; metformin, the clear prescription and hydroxyzine/hydralazine were unflagged. Round-2 measurements stand: n = 10 images; Groq-first 20/20, median 2.8 s; NVIDIA-first 62 s.

## 8. Validation (final runs on `aec62e0`, plus the test-only fix `794aa7c`)

| Check | Result |
|---|---|
| Backend `TESTING=1 uv run pytest -q` | **1781 passed, exit 0** (round-2 end: 1753) |
| Backend, network blocked (dead HTTP(S) proxy, Hugging Face offline) | **1781 passed, exit 0** |
| Fresh clone of `aec62e0` | 1776 passed, 4 skipped (provider-preflight tests, which need API keys), **1 failed**: the new readiness test assumed an LLM provider was configured, and a clone without keys has none. The test bug was fixed in `794aa7c` (the test now sets every component it does not test). After pulling the fix into the clone, `tests/test_api.py` gives 43 passed. The full clone suite was not re-run after this test-only change. |
| Frontend `vitest run`, `tsc -b`, `oxlint` | **141/141**, exit 0, exit 0 (3 pre-existing warnings) |
| `git diff --check 054cf16..HEAD`, gitleaks over `054cf16..HEAD` | clean, no leaks |
| Real NLI [real-NLI] | the root-cause measurements and the rejected candidate fix (section 3) |
| Real provider [real-provider][http] | 12 Groq positive-path runs; 2 Cloudflare runs through real failover; 3 Groq vision screening runs |
| Browser [browser] | Not repeated this round. The UI changes (confirmation-panel warning and flags) are covered by vitest. Round 2's browser positive and negative paths ran on the same pipeline. |

## 9. Integrity (Phase 10)

- Frozen V1 corpus is byte-identical (full hash above).
- `LIVE_APP_PROMPT_V1` (`e4a63bd3…`) and V2 are hash-pinned; V2 is the default and fails closed when missing or edited (`test_live_prompt_versions.py`).
- `data/` and `config/` are unchanged since `054cf16`.
- `data/live_medical/relationships` holds only the V1 files.
- REL-LIVE-0004 is `CANDIDATE_PENDING_RESEARCHER_APPROVAL`, approval `null`, severity `UNGRADED`.
- Audit fixtures were used only in a scratch folder outside the repository.

## 10. Decisions for the owner or reviewers

1. **NLI model.** A calibrated or better entailment model is the only safe way to reduce false withholdings. The current model both over-entails and falsely contradicts.
2. **Evidence-quality grading scheme** (section 4), or accept that R3 always abstains.
3. **Consistency proxy and cosine relevance** suitability.
4. **Salt/brand to ingredient evidence rule** (clinical).
5. **Clinical approval** of any evidence before the live app can answer.
6. **Prescription fields design** (section 6).
