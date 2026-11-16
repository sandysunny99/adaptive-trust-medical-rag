# Food guidance: claim strength and browser validation — 2026-10-22

Follows `CLAUDE_FOOD_GUIDANCE_2026-10-22.md`. Research tool output only; nothing here is clinical advice.

**Confirmations:**
- No commit, push, tag, merge or deployment was made by Claude. `.env.local` was not modified.
- HEAD is `a96e171`; `baf6c93` and `30774eb` are intact.
- FOOD-0001 is pending; REL-LIVE-0003 is pending and `UNGRADED`. No V2 file is in `data/live_medical/relationships/`.
- The research verifier `claim_verifier_v2.py` has no diff.

## 1. Fix: wording strength

Entailment does not check how strong a claim is. With the real NLI, "Avoid potassium-containing salt
substitutes" was **SUPPORTED** against a passage that lists them only as a risk factor.

**Design** (`services/claim_strength.py`):
- **Reviewed wording.** Each approved evidence chunk may carry `supported_claims` (`text` and `action`).
  FOOD-0001: one claim, action `MONITOR`.
- **Strength check.** After the NLI says SUPPORTED, a statement citing that chunk may not exceed the
  strongest reviewed action on the ladder below, and may not add certainty, a quantity or timing unless
  a reviewed claim `allows` it.

  | Level | Actions |
  |---|---|
  | 1 | risk association, monitoring |
  | 2 | caution, discuss with a clinician, keep consistent |
  | 3 | limit |
  | 4 | avoid |
  | 5 | change medication, or a personal plan |

- **Fail closed for food.** A food statement whose cited source has no reviewed wording is withheld.
- **Released food lines are the reviewed wording, not the generated wording.** The generated line only
  selects which reviewed statement applies, so a paraphrase the cue lists miss still never reaches the
  user. The generated line stays in the claims record.
- All-or-nothing release is unchanged: any withheld statement withholds the answer.

**Pushed back:** a second verification framework. The NLI, provenance, identity and pair checks are
unchanged; this adds one check after them.

**FOOD-0001 regenerated** with the reviewed wording:
- The label passage is unchanged (SPL v12, section 5.5, content hash `f2cbcbc0…`).
- The evidence and manifest hashes changed because the evidence file now holds the reviewed wording.
- Still `CANDIDATE_PENDING_RESEARCHER_APPROVAL`; the tracked fixture copy is identical.

## 2. Results

| Check | Kind | Result |
|---|---|---|
| `tests/test_claim_strength.py` (18) | deterministic, no model | PASSED |
| `tests/e2e/test_live_evidence_provenance.py` (26) | real PubMedBERT NLI | PASSED |
| same file | stand-in NLI | PASSED |
| How each overstated line was withheld (real NLI) | — | "avoid": NLI SUPPORTED, **strength check rejected**; "do not use": NLI CONTRADICTED; "limit … 1 g per day": NLI UNSUPPORTED; overstated conclusion: withheld |
| Backend suite (`TESTING=1`) | stand-in NLI, simulated providers | PASSED 1609 |
| ruff, Bandit | static | PASSED |
| gitleaks: diff and new untracked files | static | no leaks |

`test_live_failure_semantics.py` failed four times at first, as expected: its fixture answer includes a
food item citing a synthetic chunk without reviewed wording, which now fails closed. Its fixture chunk now
carries a commented reviewed record (`AVOID`, allowing timing and quantity). The same failure exposed a
real gap, now fixed: unbracketed `Source 1` markers were not recognised when building the released lines.

## 3. Browser validation (built-in browser, 127.0.0.1:5173, real backend)

| Scenario | Result |
|---|---|
| A. Lisinopril with synthetic context (age 67, type 2 diabetes, chronic kidney disease), FOOD-0001 pending | PASSED: "Food & Diet Guidance — No food or dietary guidance could be verified … This does not mean there are no food or dietary issues"; no food card; abstention; no links. Screenshot `browser_food_not_verified_notice.jpg` |
| B. Verified, isolated | PASSED. Real pipeline output (real NLI, FOOD-0001 approved in a temp folder only) rendered by the real `ResultPanel` on a temporary dev page (deleted afterwards). The card shows the reviewed sentence and a link to the exact set ID (`target=_blank`, `rel="noopener noreferrer"`); a click on that link opened the DailyMed lisinopril label at that set ID. The overstated "avoid" output abstains, shows the notice, and never displays the "avoid" line. Screenshot `browser_food_verified_fixture_card.jpg`; output `food_pipeline_output_verified_and_overstated.json` |
| C. Lisinopril + spironolactone | PASSED: abstains; no interaction card; no links. In the live corpus it stops at the source-identity gate before the pair gate (the pair gate is covered by tests) |
| D. Warfarin + ibuprofen | PASSED: abstains; "Excluded sources (2)"; food notice; no food card; no links |

## 4. Loading several approved datasets

The loader reads one V2 dataset with fixed file names, so **copying FOOD-0001 into
`data/live_medical/relationships/` would overwrite REL-LIVE-0003's files, or the reverse**. Nothing is
approved, so nothing is affected today.

Safe path, not built now because no approval is pending:
- Each approved dataset in its own subfolder with its own manifest and approval.
- The loader validates each independently and rejects duplicate chunk IDs and record IDs across sets.
- The live store records which dataset (and approval) each chunk came from.
- Until then: approve **one** candidate at a time, or merge by hand with a fresh manifest naming both approvals.

## 5. Remaining

1. The cue lists can miss a paraphrase in non-food statements (conclusion, warnings). Food lines are safe
   because their reviewed wording is what gets released; other single-drug statements rely on the NLI plus
   the cue lists.
2. Cosmetic: the citation label uses the SPL's official title, which is the long "These highlights do not
   include…" text.
3. FOOD-0001 approval is yours: confirm section 5.5 on DailyMed and the reviewed sentence in the
   manifest, then follow `how_to_approve`.
