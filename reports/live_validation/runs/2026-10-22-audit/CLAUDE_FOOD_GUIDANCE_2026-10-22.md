# Food & Diet Guidance — 2026-10-22

Earlier reports are unchanged. Research tool output only; nothing here is clinical advice.

**Confirmations:**
- No commit, push, tag, merge or deployment was made by Claude.
- `.env.local` was not modified. HEAD is `a96e171`; `baf6c93` and `30774eb` are intact.
- The frozen corpus is unchanged.
- REL-LIVE-0003 is pending and `UNGRADED`. FOOD-0001 is pending; nothing was approved.

## 1. Root cause (proven)

Food guidance already existed end to end: the answer schema (`food_guidance`), the prompt
(`LIVE_APP_PROMPT_V1.txt`), per-item verification, and the UI "Food & Administration" card. Patient
context already reached retrieval and the prompt, with "fields not provided are unknown".

It could **never** be released. The live path verified every statement with the drug-pair identity map:
- A single-drug statement (food, warning, adverse reaction) has no pair, so its identity is `UNAVAILABLE`.
- `claim_verifier_v2` turns `UNAVAILABLE` into `UNSUPPORTED`.

Measured with the real PubMedBERT NLI against lisinopril label section 5.5: a salt-substitute claim had
entailment 0.985, but came out UNSUPPORTED on the live path and SUPPORTED without the pair check.

## 2. Decisions (asked of the user)

| Question | Decision |
|---|---|
| Claim rule | **Changed**: only statements naming two or more drugs need an approved relationship record; single-drug statements are judged on cited, identity-verified evidence (citation, provenance, trust and NLI). Live app only; the research verifier is unchanged. |
| Release | **All-or-nothing kept**: food guidance is shown only when the whole answer verifies. |
| Evidence | **FOOD-0001 prepared, pending**; an approved manifest may list standalone evidence chunks. |

Pushed back (not built): a separate food evidence model, SSE stage, action-category engine and five UI
states. Without approved food evidence they would show nothing, and the existing pipeline already carries
food items, citations and abstention.

## 3. Changes (uncommitted)

| File | Change |
|---|---|
| `services/live_application.py` | Pair identity map passed only when a statement names two or more drugs |
| `verification/canonical_identity.py` | `_drug_mentions` made public as `drug_mentions` (no behaviour change) |
| `services/live_relationships.py` | Approved V2 manifest may list `standalone_evidence_chunks` (same validation, hashes and approval) |
| `scripts/build_food_0001_candidate.py` | Builds FOOD-0001 from the live DailyMed SPL, reusing the REL-LIVE-0003 builder |
| `reports/.../food_0001_candidate/` and `tests/fixtures/food_0001_candidate/` | The pending candidate and a tracked, identical test copy |
| `frontend/.../ResultPanel.tsx` | Food card shows each statement and timing, and links each `[Source N]` to the exact verified document (or says why not). When nothing is verified: "No food or dietary guidance could be verified … This does not mean there are no food or dietary issues." |
| `frontend/.../services/evidenceDisplay.ts` | `verifiedHref` moved here and shared (no copy); `citedSourceNumbers` |
| Tests | 4 backend e2e (pending loads nothing, supported release, pair statement still abstains, fixture is real label text); 3 frontend |

## 4. FOOD-0001

| Field | Value |
|---|---|
| Source | Lisinopril tablet SPL `34ebeea1-6812-4697-84c4-b2ae4f39e55f`, v12, section **5.5 Hyperkalemia**, verbatim (424 chars), hash `f2cbcbc0…` |
| Supported wording | Potassium-containing salt substitutes are listed as a **risk factor** for hyperkalemia with lisinopril; the label advises periodic serum potassium monitoring |
| Not supported | avoiding all potassium foods, any limit or diet plan, any severity grade, changing a medicine |
| Patient-context relevance | the passage also lists renal insufficiency and diabetes mellitus as risk factors |
| Status | `CANDIDATE_PENDING_RESEARCHER_APPROVAL`; separate from REL-LIVE-0003 |

Only one V2 dataset is loaded at a time, so approving both candidates later means merging their files.

## 5. Results

| Check | Kind | Result |
|---|---|---|
| Supported case: FOOD-0001 approved in a temp folder, real pipeline | **real PubMedBERT NLI** and stand-in NLI | PASSED: answer released; every claim SUPPORTED, including the food item; evidence links to the exact DailyMed set ID |
| Pair statement without a relationship record | both NLI modes | PASSED: abstains, identity unavailable |
| Unsupported case, live backend, frozen corpus (lisinopril; warfarin + ibuprofen; lisinopril + spironolactone) | real backend over HTTP/SSE | PASSED: abstention, no score, 0 food items, no LLM call |
| Backend suite (`TESTING=1`) | stand-in NLI, simulated providers | PASSED 1586 |
| Provenance suite | real and stand-in NLI | PASSED 21 / 21 |
| Frontend vitest / tsc / lint | jsdom / static | PASSED 126 / exit 0 / 3 baseline warnings |
| ruff, Bandit | static | PASSED |
| gitleaks (diff, and new untracked files) | static | no leaks |
| Browser | — | NOT RUN (you were using the shared pane; the UI is covered by component tests) |

## 6. Limits

1. **NLI does not check action strength.** It accepted "avoid salt substitutes" against "risk factor"
   wording (entailment 0.985). Generated wording beyond `supported_claim` is not caught automatically;
   the reviewer note in the manifest says so.
2. Food guidance appears only if the whole answer verifies (all-or-nothing kept).
3. No approved food evidence exists yet: the live app shows the "could not be verified" notice.
4. No warfarin food candidate was prepared. It needs its own label passage capture; warfarin + ibuprofen
   is a drug-drug question and does not support food wording.
