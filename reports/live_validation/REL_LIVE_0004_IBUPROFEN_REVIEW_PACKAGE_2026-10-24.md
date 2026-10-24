# REL-LIVE-0004 (warfarin ↔ ibuprofen): evidence-review package, 2026-10-24

Research material for an authorized reviewer. It is not clinical advice and does not approve anything.

**Status, unchanged by this package:** REL-LIVE-0004 is `UNGRADED` and its manifest is `CANDIDATE_PENDING_RESEARCHER_APPROVAL`, with no approver. It is not in `data/live_medical` and is not loaded by the live application. The project owner chose the ibuprofen label below as the preferred source for the next candidate revision on 2026-10-24. That is a source selection only.

## 1. Sources

| | Current candidate source | Selected ibuprofen source | Alternative (not independent) |
|---|---|---|---|
| Set ID | `884cdbf6-0a52-4126-8e14-b0d7c9367e33` | `404df13d-4ada-4324-9eed-e21f5d5043a4` | `b7e4f477-82b5-4c5c-8d3e-99c48cc090f4` |
| Label | Warfarin sodium tablets, SPL v8 | "Ibuprofen Tablets, USP 300 mg, 400 mg, 600 mg and 800 mg", SPL v6 | "Ibuprofen Tablets, USP Rx only", SPL v2 |
| Labeler | (see candidate manifest) | REMEDYREPACK INC. (repackager) | Proficient Rx LP (repackager; text names Aurobindo Pharma Limited as manufacturer) |
| Version check | v8, latest when captured on 2026-10-22 | v6 = latest in DailyMed history; effective 2026-10-15; history published 2026-10-19 | v2 = latest; effective 2026-10-01 |
| Active moiety (SPL) | warfarin | IBUPROFEN | IBUPROFEN |
| Section | 7.3 Drugs that Increase Bleeding Risk | Warfarin-type anticoagulants | Warfarin-type anticoagulants |
| Section text SHA-256 | `23081251…` (in the candidate) | `1f9d10d08f4a95040c4661d90b2d8f23585b26446a10bd27fe769a715fd5f360` | `2b48c7ca9f46f62b9814a65a95e7e4035328e56976ed67accf43600dddc1ea0a` |
| SPL XML SHA-256 at capture | n/a | `f951fb2e1e2cf07e0be92f934c6dad1a6e43c91b5c54823c0f62a0644ac9f063` | `a495b0ed0b17acf3bb75c2d2a10239b5ca251412cb7e632c547c38882a8a4441` |
| URL | `https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=884cdbf6-0a52-4126-8e14-b0d7c9367e33` | `https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=404df13d-4ada-4324-9eed-e21f5d5043a4` | `https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=b7e4f477-82b5-4c5c-8d3e-99c48cc090f4` |

**How the sources were verified (2026-10-24):**
- Both ibuprofen documents were fetched from the DailyMed SPL service (`/services/v2/spls/<setid>.xml` and `/history.json`).
- The `setId` in each XML equals the requested set ID, and the version is the latest in its history.
- The title and SPL `activeMoiety` were read from the document.
- The section was extracted with `scripts/build_rel_live_0003_candidate.py:text_of` (as of `76df3f2`), whitespace collapsed, nothing else changed. "ibuprofen" and "warfarin" each appear as whole words.

**Independence:** both ibuprofen labels are repackager labels. Their section texts are identical apart from capitalisation ("Ibuprofen tablets" vs "ibuprofen tablets"). Treat them as one source, not as corroboration.

The earlier ibuprofen label `72ec2491-924d-460f-9510-62d624d54b59` (v17) is unusable. Words are run together inside its source XML ("Ibuprofentablets"), so it is not used.

## 2. Exact source passage (404df13d v6, "Warfarin-type anticoagulants")

> Several short-term controlled studies failed to show that Ibuprofen tablets significantly affected prothrombin times or a variety of other clotting factors when administered to individuals on coumarin-type anticoagulants. However, because bleeding has been reported when Ibuprofen tablets and other NSAIDs have been administered to patients on coumarin-type anticoagulants, the physician should be cautious when administering Ibuprofen tablets to patients on anticoagulants. The effects of warfarin and NSAIDs on GI bleeding are synergistic, such that the users of both drugs together have a risk of serious GI bleeding higher than users of either drug alone.

(This is the FDA labeling text as published on DailyMed, quoted for review.)

## 3. Supporting and limiting statements

| The passage says | Kind |
|---|---|
| Short-term controlled studies did **not** show a significant effect on prothrombin times or other clotting factors | **Limiting.** It does not support any claim that ibuprofen raises INR or prothrombin time. |
| Bleeding **has been reported** with ibuprofen and other NSAIDs in patients on coumarin-type anticoagulants | Supporting, at the level of case reports |
| The physician should be **cautious** when giving ibuprofen to patients on anticoagulants | Supporting, at the level of caution (a reviewed action would be `CAUTION`) |
| Warfarin and NSAIDs are **synergistic** for GI bleeding; together, the risk of **serious GI bleeding** is higher than with either alone | Supporting, at the level of a risk association, for the NSAID class with warfarin |

**Wording a revised candidate could carry**, if a reviewer agrees. It stays inside the passage:
"Bleeding has been reported when ibuprofen is used by patients taking warfarin-type anticoagulants, and the label advises caution; using warfarin with an NSAID such as ibuprofen raises the risk of serious gastrointestinal bleeding. Short-term studies did not show that ibuprofen changed prothrombin times."

**Not supported by this passage:**
- an INR or prothrombin-time increase;
- any severity grade or numerical risk;
- an instruction to avoid the combination;
- stopping, starting or changing a dose;
- monitoring frequency;
- any population-specific statement.

## 4. Unresolved gaps

1. **Severity grade.** Must be assigned by an authorized clinician or pharmacist using the project's documented grading method. The record stays `UNGRADED` until then.
2. **Approver.** A named reviewer must set `approved_by` and `approved_at` in the manifest. The loader rejects the dataset until then, and it also rejects an `UNGRADED` record even with an approved manifest.
3. **Two passages to reconcile.** The current candidate cites the warfarin label (section 7.3, "closely monitor"); the ibuprofen label says "be cautious" and adds the GI-bleeding synergy and the negative prothrombin finding. The reviewer decides whether the revised record cites one or both, and which reviewed action (`MONITOR` / `CAUTION`) applies.
4. **Food guidance.** Neither passage contains food or diet guidance, so none may be released for this pair from these sources.

## 5. Steps after an authorized review (not done)

1. Rebuild the candidate with the selected source. Use the `scripts/build_rel_live_0004_candidate.py` pattern, write to a new candidate folder, and compute new hashes from the captured bytes.
2. The reviewer records the severity grade and approval in the manifest.
3. Copy the three files into their own folder, `data/live_medical/relationships/v2/rel_live_0004/`. Never copy over another dataset's files.
4. Run the relationship-loading and provenance tests.

Until then, the application keeps abstaining on this pair when no approved evidence exists. That abstention is not a finding that the combination is safe.
