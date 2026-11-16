# Warfarin + ibuprofen: source identity and the positive path — 2026-10-22

Research tool output only; nothing here is clinical advice.

**Confirmations:**
- No commit, push, tag, merge, deployment or approval was made by Claude. `.env.local` was not modified.
- The frozen corpus and `baf6c93` / `30774eb` are unchanged.
- REL-LIVE-0003, FOOD-0001 and the new REL-LIVE-0004 are all pending.

## 1. Root cause (confirmed in code, not a defect)

- **Placeholders.** `SPL-WARFARIN-001` and `SPL-IBUPROFEN-001` are frozen-corpus records with placeholder
  URLs (`setid=example-warfarin`, `setid=example-ibuprofen`). `services/live_source_links.py` classifies
  `setid=example-` as `PLACEHOLDER`, which maps to `REJECTED_SOURCE_IDENTITY`. The eligibility loop in
  `services/live_application.py` excludes such chunks before trust scoring.
- **"Not run".** With zero eligible chunks, `execute()` takes the pre-LLM abstention branch ("none has a
  verified source identity") and returns. Relationship verification, generation, claim verification and the
  safety gate therefore do not run. This is the intended order of gates.
- **No validator change.** The rejection is correct: those URLs do not identify a document.

**Pushed back:** a new stage-status vocabulary (`SKIPPED_NO_ELIGIBLE_EVIDENCE`, …). The UI already separates
a failure (red, "(failed)") from "Not run", and the abstention reason names the failed prerequisite.

## 2. Authentic sources (DailyMed, captured 2026-10-22)

| Label | Set ID | Version | Section | Usable as a record source? |
|---|---|---|---|---|
| Warfarin sodium tablets | `884cdbf6-0a52-4126-8e14-b0d7c9367e33` | 8 (Jun 30, 2026) | 7.3 Drugs that Increase Bleeding Risk (887 chars) | **Yes**: names both drugs; "closely monitor patients receiving any such drug with warfarin" |
| IBU (ibuprofen) tablets | `72ec2491-924d-460f-9510-62d624d54b59` | 17 (May 15, 2026) | Warfarin-type anticoagulants (667 chars) | **No**: the XML runs words together ("Ibuprofentablets"), so the text never names "ibuprofen" as a whole word, and the loader's both-drugs check rejects it. Not "repaired". |

RxNav: 11289 = warfarin, 5640 = ibuprofen (both active).

## 3. REL-LIVE-0004 (pending)

| Field | Value |
|---|---|
| Builder | `scripts/build_rel_live_0004_candidate.py` (reuses the REL-LIVE-0003 helpers) |
| Candidate | `rel_live_0004_candidate/`; tracked copy in `tests/fixtures/rel_live_0004_candidate/` |
| Record | warfarin ↔ ibuprofen, INTERACTION, BIDIRECTIONAL, severity **UNGRADED** (the loader rejects it until graded) |
| Chunk | `DAILYMED-884CDBF6-SPL-V8-SEC-7.3`, hash `23081251…` |
| Reviewed wording (`MONITOR`) | "Ibuprofen is listed among drugs that can increase the risk of bleeding when used with warfarin, and the label advises closely monitoring patients who receive it with warfarin." |
| Not supported | any severity grade, a numerical risk, avoiding the combination, stopping or changing either medicine |

## 4. Scenario results

All from `tests/e2e/test_live_warfarin_ibuprofen.py` (9 tests) through the real `execute()`, with
**PASSED with both the real PubMedBERT NLI and the stand-in**. Retrieval is stubbed with exact chunks;
approval exists only inside `tmp_path`.

| Scenario | Result |
|---|---|
| 1. Frozen corpus (all 14 chunks) | abstains; 12 unrelated, 2 placeholders rejected; score `null`; **no model call** |
| Shipped candidate | real label text; pending, loads nothing; even if approved, the UNGRADED record is rejected |
| 2. Verified source + approved record (test-only severity) | **relationship verification runs**; claim SUPPORTED with identity MATCH; answer released; evidence links to the exact warfarin set ID |
| Overstated pair claim ("never combine them") | withheld |
| 3. Verified source, no relationship record | abstains; identity UNAVAILABLE |
| 4. Tampered text (hash), wrong set ID, placeholder URL | fails closed: rejected at load, or loaded but never identity-verified |

**Live backend over HTTP/SSE (frozen corpus):**
- RxNorm: warfarin 11289, ibuprofen 5640.
- 14 retrieved; 12 unrelated; 2 identity-rejected; 0 eligible.
- Score `NO_ELIGIBLE_EVIDENCE`; generation not run; abstention.

This matches your screenshots.

## 5. Checks

| Check | Result |
|---|---|
| Backend suite (`TESTING=1`) | PASSED 1618 |
| ruff, Bandit | PASSED |
| gitleaks: diff and new files | no leaks |
| Browser | NOT RUN this pass: behaviour unchanged since the browser run of scenarios A–D earlier today; the positive path is covered by the e2e tests above |

## 6. Remaining

1. Three pending V2 candidates use the same file names: **approving one means copying it into the live
   folder; copying a second would overwrite the first.** Approve one at a time, or build the per-dataset
   loader described in `CLAUDE_FOOD_STRENGTH_AND_BROWSER_2026-10-22.md` first.
2. REL-LIVE-0004 needs a severity grade by your documented method, then your approval.
3. The ibuprofen label's run-together XML text is a DailyMed data quality issue; that label cannot ground a
   record until a version with proper word spacing is captured.
