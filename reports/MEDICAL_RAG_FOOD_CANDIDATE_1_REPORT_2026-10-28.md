# FOOD-CANDIDATE-1: Conditional Patient-Food Guidance (Candidate Report)

Date: 2026-10-28. Authorization: owner decisions F1–F8 of 2026-10-27 (thread message, "Owner Decisions and Implementation Authorization").

**Status: engineering candidate only.** Clinical validation is **absent**. No nutrition source is approved, so in the live configuration this candidate never releases a patient-specific food recommendation: Mode B returns `NO_APPROVED_EVIDENCE`. Fixture tests that show the release path use test-approved records built inside `tmp_path`. They show control flow, not clinical correctness or patient safety. Nothing was staged, committed or pushed.

## 1. Candidate location and starting state

| Item | Value |
|---|---|
| Candidate path | `C:\Users\sunny\food-candidate-1` |
| Logs and diff | `C:\Users\sunny\food-candidate-1-logs\` |
| How it was made | `git clone --local --no-checkout` of the Round-6 repository, `git checkout --detach 2190fb0`, `origin` remote removed |
| Round-6 overlay | 24 files copied from `C:\Users\sunny\round6-evidence-2026-10-27\candidate_tree\` after `sha256sum -c SHA256SUMS.txt` (44 OK) |
| Fingerprint before changes | `sha256sum -c r6c_fingerprint.txt`: **24 OK, 0 failed** |
| Fingerprint after changes | 23 OK; `services/live_application.py` differs, which is this candidate's own change |
| C1 cache mappings | **Not included.** C1 stays separate in `C:\Users\sunny\r7-c1-cache`. |
| Diff | `C:\Users\sunny\food-candidate-1-logs\FOOD-CANDIDATE-1.diff` (15 files; SHA-256 `5eb3bb3627bac30e6253da6a16b4cd9294217634ea8054b0584e5760d7c1f392`), relative to the fingerprint-verified Round-6 state |

Environment-only additions in the clone (not part of the diff): `.venv`, `frontend/node_modules`, and `cognee_service/model_cache/` (the pinned NLI model `pritamdeka/PubMedBERT-MNLI-MedNLI` at revision `f1b6ce2e…`, downloaded by the test run). The clone has no `.env` or `.env.local`; neither was opened or copied.

## 2. What changed

### Backend

**New: `src/adaptive_trust_medical_rag/services/patient_food.py`**
- `decide_mode(drug_names, patient_context)`: deterministic Mode A/B/C/D from the two inputs alone. Usable context is a **CONFIRMED** condition, dietary instruction or food allergy/intolerance. Age, sex, medication allergies (`known_allergies`) and unconfirmed items never make context usable.
- `context_items`, `context_report`: each item with its source (`USER_ENTERED` / `DOCUMENT_EXTRACTED`), confirmation, whether it was used and why not.
- `medication_view`: the patient context the medication branch sees. For a legacy request it is exactly what the branch saw before (tested). The two new food-only fields and any unconfirmed condition item are left out.
- `load_patient_food_store`: loads approved `CONDITION_DIET` records from `data/live_medical/patient_food/` (the folder **does not exist**, so the live store is empty). A dataset loads only if its manifest is `APPROVED` with a named approver, its **source and permitted use** are approved with a named approver, and the records file matches the manifest SHA-256. Each record needs a named reviewer, an approved classification (`recommended | limit | avoid | insufficient_evidence`), a content-hash-matched passage with a **verified source identity** (the existing `check_source_identity`), and the passage must itself name the food and the basis term. Failing records are rejected and listed.
- `patient_food_stage`: LLM-free. Matches records to confirmed items by exact term after case/whitespace folding (no fuzzy or broader-condition matching). A food-allergy item can only match a food-allergy record, never a condition-diet record. Releases the record's reviewed wording verbatim, its approved classification, qualifiers, scope and source passage. Marks an item `conflict` (keeping `approved_classification`) when another matched record for the same food has a different direction, a confirmed dietary instruction or food allergy names the same food, or a released medication-food warning names it. It never picks a side.

**`services/live_application.py`** (87 insertions, 28 deletions relative to Round 6)
- The patient-context input screen now also covers the two new fields and item objects (same `_screen_note` check).
- After the input screen and any image confirmation, `decide_mode` runs and an `analysis_mode` SSE event is emitted. Mode C ends with `PATIENT_ONLY_NOT_SUPPORTED` and Mode D with `MEDICATION_INPUT_REQUIRED`, before any normalisation, retrieval or model call.
- The medication retrieval query and prompt use `medication_view(patient_context)` (F7: unchanged for existing inputs). Prompt files and hashes are untouched.
- Both abstention events and the answer carry `analysis_mode`, `analysis_mode_reason`, `patient_food_status`, `patient_food_reason`, `patient_food_guidance` and `patient_context_items`. On any abstention the status is `WITHHELD_MEDICATION_ABSTAINED` (Mode B) or `NOT_APPLICABLE`. On a released answer, the stage runs **after** the medication gate and reads only the released `food_guidance` lines.
- `_load_models` loads the patient-food store separately from retrieval, so its records never become medication evidence.

**`api/live_schemas.py`** (additive)
- `ContextItemInput {text, source, confirmation}` with both `source` and `confirmation` required, `extra="forbid"`. `MODEL_INFERRED` is not accepted.
- `PatientContextInput`: `known_conditions: list[str | ContextItemInput]` (a plain string keeps the old contract and is read as user-entered and confirmed); new `dietary_instructions` and `food_allergies_intolerances` (item objects only); `known_allergies` documented as medication allergies.
- `AnalyzeResponse`: `food_guidance_status` (already emitted, previously untyped), and the six new fields above with typed patient-food item and context-report models.

### Frontend

- `types/index.ts`: `ContextItem`, `AnalysisMode`, `PatientFoodStatus`, `PatientFoodItem`, `PatientContextItemReport`. `FoodGuidance.food_relationship` is now `string`, with `FOOD_RELATIONSHIP_VALUES` listing the 7 values both live prompts (V1, V2) request. The backend does not restrict this field, so any other value is shown as received, not normalised. The old union (`WITH_FOOD`, `SPECIFIC_TIMING`, …) matched neither prompt.
- `ResultPanel.tsx`: the medication-food section is titled **"Medication–food interactions"** in every mode, with its empty-state wording no longer mentioning diet. A **"Patient-specific food guidance"** section appears only when `patient_food_status` is present and not `NOT_APPLICABLE`: one status line when there are no items, otherwise the reviewed wording, reason, classification or conflict, qualifiers and the verified source link. **Verified patient considerations** (F8) are rendered only when `gate_decision === 'release'`. **"Patient context used"** lists each item with its confirmation and source, and why an item was not used.
- `useAnalysis.ts`: handles `analysis_mode` and keeps the patient-food fields of an abstention.
- `WorkspacePage.tsx`: "Medication allergies", "Dietary instructions" and "Food allergies or intolerances" inputs. The last two are sent as `USER_ENTERED` and `CONFIRMED` items. With patient details but no drug, the disabled button explains that patient-only food guidance is not supported in this version.
- `exportService.ts`: the section is renamed. The patient-food section is exported without the patient input it quotes (the matched context text and typed instructions are omitted, and `patient_context_items` is dropped), keeping the existing "exports leave patient context out" rule.

### Existing tests changed (wording or behaviour the owner asked to change)

- `tests/api/test_v6_checkpoint4.py::test_4_empty_list_rejected`: now expects `MEDICATION_INPUT_REQUIRED` (Mode D) instead of `NO_VALID_DRUGS`. The image path with an empty confirmed list still returns `NO_VALID_DRUGS`, and its tests are unchanged.
- `frontend/src/components/ResultPanel.test.tsx`: three food-status wording expectations updated to the "medication-food" wording.

## 3. Validation (actual commands and results)

| Check | Command (in the clone) | Baseline (Round-6 state, before changes) | Candidate |
|---|---|---|---|
| Backend tests | `uv run pytest -q -p no:cacheprovider -o log_cli=false` | 1898 passed, **5 failed**, 4 skipped, 1 xfailed (27 min 31 s) | **1961 passed**, 5 failed, 4 skipped, 1 xfailed (39 min 43 s). The 5 failures are the same 5 baseline tests; +63 passed are the new tests (49 DET + 14 SCR/FIX); no previously passing test fails |
| New backend tests only | `pytest tests/test_patient_food.py tests/e2e/test_patient_food_pipeline.py tests/api/test_v6_checkpoint4.py` | n/a | 79 passed |
| Frontend tests | `npx vitest run` | 145 passed (22 files) | **159 passed** (22 files) |
| TypeScript | `npx tsc -b` | exit 0 | exit 0 |
| Frontend lint | `npx oxlint` | 3 warnings (react set-state-in-effect) | 3 warnings, the same pre-existing ones; none new |
| Ruff | `uv run ruff check` on the changed and new Python files | n/a | All checks passed |
| Bandit | `uv run bandit -q -ll` on the changed and new source files | n/a | exit 0, no medium/high findings |
| Protected paths | `git diff --stat -- data config experiments src/adaptive_trust_medical_rag/prompts` | — | Only `experiments/nli_eval_round5/replay_live_policy.py`, which is the Round-6 overlay file (fingerprint OK), not this candidate |
| Source checkout | `git status --porcelain` before vs after; `sha256sum -c r6c_fingerprint.txt` there | — | HEAD `2190fb0`; fingerprint 24 OK; the only new entries are two reports from the separate C2/M1 thread |

**Baseline failures (present before any change, in the clone only).** The same suite passed in the original Round-6 checkout (1907 passed, 1 xfail, `r6c_backend.log`), so these come from the clone's environment, not from this candidate:
- `tests/test_model_selector.py` (3 tests): HTTP 400 where 200 is expected. The model catalog marks providers unavailable without `.env.local`, which the clone deliberately does not have.
- `tests/e2e/test_live_failure_semantics.py::test_claim_verifier_failure_does_not_skip_retrieval`: `embedding_mode` is `real`, not `testing_stub`.
- `tests/e2e/test_v6_c7_image_full_medical_rag.py::test_1_full_rag_happy_path`: a trust-factor expectation (`query_relevance` in missing factors).
- The 4 skips are the provider-connectivity checks that need `.env.local`, as in C1.

Test-type labels used in the new backend tests: **DET** (deterministic unit tests, `tests/test_patient_food.py`), **SCR** (scripted model and retrieval stubs through `execute`), **FIX** (test-approved FOOD-0001 plus a TEST-ONLY patient-food record in `tmp_path`, real `ClaimVerifierV2`, scripted model). No test uses a real model or live retrieval. The new tests were written before the backend change and could not pass without it (the module did not exist), but I did not record a separate red run.

## 4. Requirement coverage

| Requirement | Evidence |
|---|---|
| Mode selection is deterministic and independent of the LLM | DET `test_det_mode_is_decided_from_the_two_inputs_alone` (12 cases) |
| Age/sex alone does not trigger Mode B | same test, `age/sex` and `known_allergies` cases |
| Confirmed conditions, instructions and food allergies trigger Mode B | same test |
| Mode A never emits patient-food items; medication-food warning stays in `food_guidance` | DET `test_det_mode_a_never_emits_patient_food_items`; FIX `test_fix_mode_a_releases_the_medication_food_warning_and_no_patient_food` |
| Mode B without approved records → `NO_APPROVED_EVIDENCE`, no items | DET and FIX tests; the live folder has no dataset (`test_det_the_live_data_folder_has_no_patient_food_dataset`) |
| Matching test-approved record → exact reviewed wording and source | DET `test_det_a_matching_record_releases_its_exact_reviewed_wording_and_source`; FIX `test_fix_mode_b_releases_the_exact_reviewed_record_…` |
| Unconfirmed extracted context cannot trigger a recommendation | DET `test_det_an_unconfirmed_extracted_condition_cannot_trigger_a_recommendation`; SCR `test_scr_unconfirmed_context_alone_is_mode_a` |
| Mode C: no LLM call, no retrieval | SCR `test_scr_mode_c_runs_no_normalisation_retrieval_or_model` |
| Mode D: no retrieval or generation | SCR `test_scr_mode_d_says_what_is_needed_and_runs_nothing` |
| Medication abstention → `WITHHELD_MEDICATION_ABSTAINED` | FIX `test_fix_medication_abstention_…`; SCR `test_scr_pre_generation_abstention_in_mode_b_…` |
| Food stage never changes medication claims, gate or abstention | FIX `test_fix_the_medication_answer_is_identical_whatever_the_patient_food_stage_finds` (14 medication fields JSON-equal); FIX abstention reason and claims equal in Mode A and Mode B |
| Medication-food warnings separate from condition-diet guidance | FIX Mode A test; records never join retrieval (`test_scr_patient_food_records_never_join_medication_retrieval`) |
| Explicit conflict outcome | DET tests for an instruction, opposite records and a medication-food warning; FIX Mode B test |
| Unrelated, unreviewed or unapproved citations cannot support a recommendation | DET loader rejection matrix (8 cases) and unapproved-manifest matrix (4 cases) |
| Patient considerations rendered only when verified | vitest `ResultPanel patient considerations` (2 tests) |
| UI sections, statuses and types tested | vitest: 7 patient-food tests, 2 workspace form tests, 1 hook test, 2 export tests |
| Existing medication and failure-semantics tests still pass | backend full-suite row above |

## 5. Known limitations and open items

- **No real output in the live configuration.** Real patient-food recommendations need F2: approval of a nutrition source and its permitted use, a review and provenance procedure, reviewed records with exact wording, and named reviewers.
- **Matching is exact-term only.** "CKD stage 3" does not match a "chronic kidney disease" record. That is deliberate (no inferred equivalence), but it will under-match until a terminology mapping is approved separately.
- **Conflict detection is a word match.** A dietary instruction or medication-food line that names the same food is reported as a conflict even if it agrees. It over-reports, by design, rather than choosing a direction.
- **Unconfirmed condition items are now kept out of the medication prompt and retrieval query.** This affects only the new item format; legacy string conditions reach the medication branch exactly as before (tested).
- **Response `input_mode` is still hard-coded to `direct_drugs`** (pre-existing, out of scope).
- **Browser (LIVE) check not run.** The Playwright MCP server failed to connect in this session, and no live model was called. No real-model or browser result is claimed.
- The metamizole and Zorbitrex identity-gate blockers are unaffected and still open. C2, M1 and C3 were not touched.

## 6. Protected items

Not modified: frozen evaluation inputs and labels, prompt files and their hash manifests, the NLI model revision, trust formula and thresholds, evidence eligibility, citation requirements, medication safety and abstention gates, the live corpus, the relationship datasets and approval manifests (FOOD-0001 stays `CANDIDATE_PENDING_RESEARCHER_APPROVAL`), the original Round-6 checkout, the C1 clone and the C2/M1/C3 work. No nutrition data was fetched or added.

Stopping here, as authorized. Next steps (C2, M1, C3, any nutrition source) need separate authorization.
