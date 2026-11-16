# Medical RAG round 4: NLI verifier evaluation and validation closure (2026-10-26)

Research prototype. Engineering tests and this model comparison do not establish clinical correctness, clinical safety, regulatory compliance or production readiness. No evidence was graded or approved. **The live verifier, its default model and every gate are unchanged.**

## 1. State

- **Commits:** branch `wip/pre-threads-20261022-1440`. The round started at `794aa7c` (as the round-3 report said) and ended at `a4c7ae7`, adding 2 local commits. Both are evaluation artifacts only; no application code changed. Nothing was pushed.
- **Preserved, untouched:** the 3 stale `experiments/runs/live-smoke-v1/*` files and the untracked user files.
- **`.env` / `.env.local`:** not opened in any form.
- **Integrity:**
  - Frozen V1 corpus is `1fdb0be65a1a2cf3d2847bf68fd6c5198c046760d44b23672f37dd9d78ca5578`.
  - `LIVE_APP_PROMPT_V1` is `e4a63bd3…` and V2 is `d1b3d60d…`. Both are unchanged and checked at load.
  - `data/` and `config/` are unchanged since `054cf16`. `data/live_medical/relationships` holds only the V1 files.
  - REL-LIVE-0004 is `CANDIDATE_PENDING_RESEARCHER_APPROVAL`, approval `null`, severity `UNGRADED`.
- **Verifier as inspected (Phase 0):**
  - Model: `pritamdeka/PubMedBERT-MNLI-MedNLI` @ `f1b6ce2e0d49f295b4cbcdc56c01b5fab6d068ab`, BertForSequenceClassification, `id2label {0: contradiction, 1: entailment, 2: neutral}`. Labels are mapped by name, not by index.
  - Inference: `claim_verifier_v2.ClaimVerifierV2._evaluate_pair` (premise = whole evidence chunk, hypothesis = claim text including its `[Source N]` marker).
  - Scores combine in `_map_to_state`, which compares the best entailment with the highest neutral and contradiction scores over **all** chunks.
  - The source-text overstatement bound is `claim_strength.source_text_violation`.

## 2. Round-3 validation gaps (Phase 1), now closed

| Check | Command / method | Result |
|---|---|---|
| Fresh clone of `794aa7c`, full suite | isolated clone; `uv sync`; `TESTING=1 uv run pytest -q -p no:cacheprovider -o log_cli=false -rs` | **1777 passed, 4 skipped, exit 0**; `git status` clean afterwards. The 4 skips are `test_provider_connectivity_preflight` (GROQ, GEMINI, HF_TOKEN, CLOUDFLARE keys not set in a clean clone). |
| Browser E2E [browser][real-provider] | Playwright (chromium) against the UI on :5180 and a backend on :8020 using test-approved evidence in a scratch folder outside the repo; backend at `a4c7ae7` (same application code as `794aa7c`) | **All pass** (below) |

| Flow | Observed in the browser |
|---|---|
| Negative: warfarin + ibuprofen (placeholder sources) | "The system abstained from answering."; "Trust score: Not computed (no eligible evidence)"; food: "was not assessed, because the analysis stopped before an answer was generated" |
| Positive: lisinopril + spironolactone | "Claim verification (10 of 10 verified)"; trust 0.66; verified DailyMed link (`setid=34ebeea1-…`); food: "contains no food or dietary guidance" |
| Error: a script tag typed as a drug name | "did not pass security checks, so nothing was analyzed" |
| Vision: synthetic image with an injected line (real Groq vision) | warning banner shown; "Flagged: read from text that looks like instructions to the system"; cyanide `Status: UNCERTAIN`, metformin `DETECTED`; **Confirm disabled** until reviewed |
| Vision: after removing cyanide and confirming metformin | analysis ran on metformin only (RxCUI 6809), abstained (no eligible evidence); cyanide appears nowhere in the results |

Screenshots are in the session scratchpad (`e2e_shots/`), not committed.

**Unverified text after an abstention.** Failed statements appear only in the "Claim verification" list. Each is marked with its failed state (UNSUPPORTED, AMBIGUOUS and so on, never "Verified") and its reason. On an abstention the food section shows a status sentence, never generated food text. The per-claim list is a read-only display that feeds no other component (code review of `ResultPanel.tsx`; `ResultPanel.test.tsx`).

## 3. Frozen evaluation set (Phase 2)

`experiments/nli_eval_round4/NLI_EVAL_SET_V1.jsonl` (SHA-256 `bd23fe48…f4ff`, committed in `6b5c992` **before** any candidate ran; LF pinned):
- **42 pairs** over real DailyMed SPL text from the repository's candidate fixtures:
  - **Frozen evaluation split:** lisinopril §5.5 and §7.1, 34 pairs.
  - **Dev split:** warfarin §7.3, 8 pairs. The split is by source document.
- **Labels:** 14 ENTAILMENT / 24 NEUTRAL / 4 CONTRADICTION.
- **Categories:**
  - A: true support (direct, paraphrase, pair, wrong section).
  - B: absent, other outcome, other pair, class-to-specific.
  - C: contradiction, and overstatements (mandatory, universal, may → always, action, timing, quantity).
  - D: the six known round-3 failures, with their recorded scores.
- **Label provenance: `audit_author_ai`, `review_status: UNREVIEWED`.** The labels were written by the audit author (an AI assistant). They are a development reference only, not clinician-validated ground truth, and must be independently adjudicated before they decide a model selection.

## 4. Candidates (Phase 3)

| Model | Revision | License / access | Labels | Status |
|---|---|---|---|---|
| `pritamdeka/PubMedBERT-MNLI-MedNLI` (baseline) | `f1b6ce2e…` | no license field on the hub card | named, 3-class | evaluated |
| `cnut1648/biolinkbert-mednli` | `f9f4a9d1…` | Apache-2.0 | named, 3-class | evaluated (card: MedNLI eval accuracy 0.879, test 0.861) |
| `cnut1648/biolinkbert-large-mnli-snli` | `89029f48…` | **no license declared** | named, 3-class | evaluated |
| `ygivenx/modernbert-base-mednli` | `7b0ef248…` | Apache-2.0, **gated** | — | **blocked**: HTTP 401 without a Hugging Face account that has accepted its terms (not set up on the owner's behalf) |

All models were evaluated locally from the cache at the pinned revision (`HF_HUB_OFFLINE=1`). No text was sent to any service. No pair was truncated (512-token limit).

## 5. Results (Phase 4–5)

Harness: `experiments/nli_eval_round4/run_eval.py`. Raw scores per example: `results/NLI_EVAL_RESULTS_V1.json`.

**Setting A: isolated pairs, frozen split (n = 34; false acceptance = predicted ENTAILMENT for one of the 22 unsupported claims).** CIs are Wilson 95%.

| Model | Accuracy | Macro-F1 | False acceptances | False withholdings | Median latency (CPU) |
|---|---|---|---|---|---|
| Baseline | 0.62 | 0.67 | **12/22** (35–73%) | 0/12 (0–24%) | 99 ms |
| biolinkbert-mednli | 0.59 | 0.56 | **9/22** (23–61%) | 0/12 (0–24%) | 464 ms |
| biolinkbert-large-mnli-snli | **0.76** | **0.69** | **1/22** (1–22%) | 1/12 (1–35%) | 445 ms |

**Confusion matrices** (rows = expected, columns = predicted E/N/C):
- Baseline: E 12/0/0; N 12/6/1; C 0/0/3.
- biolinkbert-mednli: E 12/0/0; N 9/5/5; C 0/0/3.
- large-mnli-snli: E 11/1/0; N 1/13/5; C 0/1/2.

**Known round-3 failures** (predicted label; entailment):

| ID | Claim | Baseline | biolinkbert-mednli | large-mnli-snli |
|---|---|---|---|---|
| E06 | lisinopril + spironolactone hyperkalemia (supported) | E 0.9997 | E 0.92 | **N** 0.04 (miss) |
| E07 | "attenuates potassium loss…" vs 7.1 (supported) | E 0.9995 | E 0.9993 | E 0.99 |
| E08 | same claim vs 5.5 (should be neutral) | **C** | **C** | N |
| E09 | hypotension on initiation (supported) | E | E | E |
| E13 | "stopped immediately in all patients" vs 7.1 | **E 0.991** | **E 0.78** | C |
| E14 | "kidney failure in all patients" | **E 0.568** | N | N |
| E15 | "thiazides stopped in all patients" | **E 0.9996** | **E 0.9986** | C |

**Setting B: replay through the application's decision logic** (ClaimVerifierV2 states plus the source-text bound; classifier swapped in the harness only; 42 claims, 14 should be released). The harness does not apply the live pair-identity check, so it **overstates** pair-claim releases compared with the live app.

| Model | Released | False releases | False withholds | Without the citation marker in the NLI input (diagnostic) |
|---|---|---|---|---|
| Baseline | 14 | E25 (true fact cited to the wrong section), E28 (class-to-specific; the live identity check withheld this pattern in round 3) | E01 (marker effect), E07 | 16 released; false releases E24, E25, E28 |
| biolinkbert-mednli | 14 | E25, E28 | E03, E07 | 13 released; false release E25 |
| large-mnli-snli | 4 | none | **10** (D01, D02, E02–E07, E10, E33) | 7 released; 7 false withholds |

**Reading:**
- The baseline over-entails in isolation. 12 of 22 unsupported or overstated claims score as entailment. The pipeline's conservative neutral rule and the overstatement bound are what keep most of them from release.
- biolinkbert-mednli is no safer than the baseline.
- biolinkbert-large-mnli-snli is the only model that rejects the known dangerous overstatements on its own (E13, E15). Inside the current conservative pipeline, though, it withholds 10 of 14 correct claims, mostly because its entailment falls below another chunk's neutral score.
- Wrong-section citations (E25) are a remaining false-release pattern for both the baseline and biolinkbert-mednli. The content is true, but it is attributed to the wrong section.
- Sample sizes are small, and the labels are unreviewed. None of these rates is a clinical false-acceptance estimate.

## 6. Recommendation (Phase 6)

| Candidate | Compatibility | False-acceptance evidence | False-withholding evidence | Calibration | Latency | Recommendation |
|---|---|---|---|---|---|---|
| Baseline (current) | in use | poor in isolation (12/22); guarded by the pipeline rules | low | not assessed (n too small) | 99 ms | **Keep, with the current gates** |
| biolinkbert-mednli | drop-in (3-class, named labels) | no better than baseline (9/22) | low | not assessed | 464 ms | Do not pursue |
| biolinkbert-large-mnli-snli | drop-in; **no declared license** | best observed (1/22) | high inside the current pipeline (10/14) | not assessed | 445 ms | **Worth a broader, separately approved study**: independently reviewed labels, a larger set across more labels, a license check, and a gated experiment on how the pipeline's neutral rule should treat it. Not for deployment. |
| ModernBERT MedNLI | unknown | — | — | — | — | Blocked (gated access) |

**No candidate qualifies for replacement.** The live verifier, default model, trust formula, thresholds, eligibility rules, source-text bound and abstention behaviour are unchanged. A replacement would need a separately authorized follow-up with a frozen artifact, reviewed labels, reproducible results, a regression suite covering the round-3 false acceptances, a rollback plan and owner approval.

## 7. Other owner decisions (Phase 7), unchanged as instructed

- Missing evidence-quality grades stay missing.
- Consistency proxy and cosine relevance: pending research review.
- Salt and brand concepts keep their exact RxCUI; the ingredient is displayed only.
- REL-LIVE-0004 and all candidates stay unapproved.
- Prescription strength, form and frequency: a separate design task.
- Food guidance keeps its five states.
- Vision screening and confirmation controls are retained.

## 8. Final validation

All runs were on `a4c7ae7` in sequence:

| Class | Check | Result |
|---|---|---|
| Unit / integration / mock-provider | `TESTING=1 uv run pytest -q` | **1781 passed, exit 0** |
| Same suite, network blocked | dead HTTP(S) proxy; Hugging Face offline | **1781 passed, exit 0** |
| Fresh clone | isolated clone of `a4c7ae7`; `uv sync`; full suite | **1777 passed, 4 skipped (provider preflight, no keys), exit 0**; clean status afterwards |
| Frontend | `vitest run`, `tsc -b`, `oxlint` | **141/141**, exit 0, exit 0 |
| Security | `git diff --check 054cf16..HEAD`; gitleaks over `054cf16..HEAD` | clean; no leaks |
| Local model evaluation | `run_eval.py` (3 models, 42 pairs, settings A and B) | section 5 |
| Real provider + browser E2E | Groq text and vision through the real UI | section 2 (4 flows, all pass) |
| Real HTTP/SSE | covered by the browser flows above | — |

The application code is unchanged since `794aa7c`. The only commits this round are `6b5c992` (evaluation set) and `a4c7ae7` (harness and results).

## 9. Remaining blockers and decisions

1. **Independent review of `NLI_EVAL_SET_V1` labels**, and a larger reviewed set, before any model decision.
2. **ModernBERT access:** accept its terms on Hugging Face and provide a token through the process environment if it should be evaluated.
3. **The license of `cnut1648/biolinkbert-large-mnli-snli`.**
4. **Wrong-section citations** (E25) are still released by the baseline pipeline. A section-level attribution check is a possible future gate, needing its own design and approval.
5. Clinical approval of evidence; the evidence-quality scheme; the salt/brand rule (all unchanged).
