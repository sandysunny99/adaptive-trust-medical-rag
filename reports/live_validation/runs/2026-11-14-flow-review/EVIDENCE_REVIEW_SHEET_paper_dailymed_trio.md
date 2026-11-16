# Evidence review sheet: the paper's three DailyMed sections

Prepared on 2026-11-14 by Claude, read-only.

**This sheet approves nothing.** No status, dataset, corpus file or `data/live_medical/relationships/` entry was changed. This is research tooling, not clinical advice.

## 1. Inventory of candidate datasets on this PC

Every dataset below was checked with the app's own validators (`live_relationships.validate_record`, `validate_evidence_chunk` and `_records_hash`; `live_source_links.check_source_identity`).

| Dataset | Path | Status | Covers | Source | Hashes | Loader verdict if approved as is |
|---|---|---|---|---|---|---|
| V1 (REL-LIVE-0001) | `data/live_medical/relationships/` | CANDIDATE_PENDING_RESEARCHER_APPROVAL | simvastatin (36567) + clarithromycin (21212): CONTRAINDICATION, CONTRAINDICATED, A_TO_B | Frozen chunk `DAILYMED-SPL-SIMVASTATIN-001-CHUNK-01` (placeholder `setid=example-simvastatin`) | records: match | Record valid, but its evidence is a placeholder, so the gate still rejects it. **Unlocks no answer.** |
| V2 candidate r1 (REL-LIVE-0002) | `reports/.../2026-10-15T0448Z-acf08ee-revalidation/relationship_v2_candidate/` (and `REVIEW_PACKAGE/files_r1`) | pending | simvastatin + clarithromycin | clarithromycin label setid `9aaffb41-…` v21 §4.5 | records: match; no evidence file | Rejected: the source chunk is not in the corpus (old layout) |
| V2 candidate r2 (REL-LIVE-0002) | `.../relationship_v2_candidate_r2/` (and `REVIEW_PACKAGE/files_r2`) | pending | simvastatin + clarithromycin, CONTRAINDICATED, BIDIRECTIONAL | setid `9aaffb41-408c-4372-8fd5-1d649450c0e9` v21 §4.5 | both match | Record and chunk valid, but **no `source_identity` record**, so the gate rejects the chunk. **Unlocks no answer** until an identity record is captured. |
| **FOOD-0001** | `reports/.../2026-10-22-audit/food_0001_candidate/` (identical copy in `tests/fixtures/`) | pending | lisinopril §5.5 Hyperkalemia (standalone label evidence, no drug-pair record) | setid `34ebeea1-6812-4697-84c4-b2ae4f39e55f` v12 | both match | Chunk valid, **identity verified** |
| **REL-LIVE-0003** | `.../2026-10-22-audit/rel_live_0003_candidate/` (identical copy in `tests/fixtures/`) | pending | lisinopril (29046) + spironolactone (9997): INTERACTION, **UNGRADED**, BIDIRECTIONAL | setid `34ebeea1-…` v12 §7.1 | both match | Chunk valid and identity verified. **Record rejected: severity UNGRADED.** |
| **REL-LIVE-0004** | `.../2026-10-22-audit/rel_live_0004_candidate/` (identical copy in `tests/fixtures/`) | pending | warfarin (11289) + ibuprofen (5640): INTERACTION, **UNGRADED**, BIDIRECTIONAL | setid `884cdbf6-0a52-4126-8e14-b0d7c9367e33` v8 §7.3 | both match | Chunk valid and identity verified. **Record rejected: severity UNGRADED.** |

No V2 dataset on this PC has `approved_by`. None has ever been committed on any branch. The `c2j-work` and `cwt-feat` worktrees have only the pending V1.

## 2. Which candidate this sheet covers, and why

This sheet covers **FOOD-0001, REL-LIVE-0003 and REL-LIVE-0004 together.**

- The paper's corpus inventory (`paper_build/results/corpus_inventory.json`, 17 items) is the 14 frozen chunks plus exactly these three DailyMed sections.
- They are the only candidates whose source identity verifies: the warfarin label and the lisinopril label.
- They are the evidence the positive-path engineering runs and the C2-series tests load from approved temporary copies.
- No single candidate covers both warfarin and lisinopril, so reviewing them as a set matches the paper.
- REL-LIVE-0002 (simvastatin) is left out: it has no identity record and would not unlock anything if approved.

## 3. One row per evidence record

All three were prepared by "Claude (AI-prepared candidate; not a reviewer)", using SPL XML from the DailyMed v2 API by set ID; the section text is the XML text with whitespace collapsed. In every row the content hash matches the text (re-computed today).

| # | Pair (RxCUI) | Relationship | Exact source | Captured | Content hash | Concerns |
|---|---|---|---|---|---|---|
| 1 | lisinopril (29046), food or label item | FOOD-0001: standalone label evidence. Supported claim: potassium-containing salt substitutes are a hyperkalemia risk factor, and periodic potassium monitoring is advised. | DailyMed setid `34ebeea1-6812-4697-84c4-b2ae4f39e55f`, LISINOPRIL TABLETS, SPL v12, §5.5 Hyperkalemia | 2026-10-22, SPL sha256 `351409a1…a7e6` | `f2cbcbc0…e204` | Not a drug pair, so it doesn't unlock a pair answer on its own. Generated food guidance must stay within the stated claim (a risk factor with monitoring, not "avoid"). Version 12 may no longer be the latest label. |
| 2 | lisinopril (29046) + spironolactone (9997) | REL-LIVE-0003: INTERACTION, BIDIRECTIONAL, **UNGRADED** | Same setid, SPL v12, §7.1 Diuretics | 2026-10-22 | `8a9bde7f…81c4` | **No severity grade**, so the loader rejects it. The evidence is the *whole* §7.1, which also covers diuretic hypotension, not only the potassium-sparing sentence; the record is a generic INTERACTION. Spironolactone is named as an example of a class. |
| 3 | warfarin (11289) + ibuprofen (5640) | REL-LIVE-0004: INTERACTION, BIDIRECTIONAL, **UNGRADED**. Supported claim: ibuprofen is listed among drugs that raise bleeding risk with warfarin, and close monitoring is advised. | DailyMed setid `884cdbf6-0a52-4126-8e14-b0d7c9367e33`, WARFARIN SODIUM TABLETS, SPL v8, §7.3 Drugs that Increase Bleeding Risk | 2026-10-22, SPL sha256 `665b5240…22a` | `23081251…396d` | **No severity grade.** Ibuprofen comes from Table 3, which is flattened into running text. The label explicitly does not support a grade, a numerical risk, avoiding the combination, or changing either medicine. Owner decision on 2026-10-27: "REL-LIVE-0004 stays UNGRADED". Version 8 may no longer be the latest. |

### Verbatim evidence text (as captured; whitespace collapsed)

1. FOOD-0001, §5.5:
   > 5.5 Hyperkalemia Serum potassium should be monitored periodically in patients receiving lisinopril. Drugs that inhibit the renin angiotensin system can cause hyperkalemia. Risk factors for the development of hyperkalemia include renal insufficiency, diabetes mellitus, and the concomitant use of potassium-sparing diuretics, potassium supplements and/or potassium-containing salt substitutes [see DRUG INTERACTIONS ( 7.1)] .
2. REL-LIVE-0003, §7.1:
   > 7.1 Diuretics Initiation of lisinopril in patients on diuretics may result in excessive reduction of blood pressure. The possibility of hypotensive effects with lisinopril can be minimized by either decreasing or discontinuing the diuretic or increasing the salt intake prior to initiation of treatment with lisinopril. If this is not possible, reduce the starting dose of lisinopril tablets [see DOSAGE AND ADMINISTRATION ( 2.2) and WARNINGS AND PRECAUTIONS ( 5.4)] . Lisinopril attenuates potassium loss caused by thiazide-type diuretics. Potassium-sparing diuretics (spironolactone, amiloride, triamterene, and others) can increase the risk of hyperkalemia. Therefore, if concomitant use of such agents is indicated, monitor the patient's serum potassium frequently.
3. REL-LIVE-0004, §7.3:
   > 7.3 Drugs that Increase Bleeding Risk Examples of drugs known to increase the risk of bleeding are presented in Table 3. Because bleeding risk is increased when these drugs are used concomitantly with warfarin, closely monitor patients receiving any such drug with warfarin. Table 3: Drugs that Can Increase the Risk of Bleeding Drug Class Specific Drugs Anticoagulants argatroban, dabigatran, bivalirudin, desirudin, heparin, lepirudin Antiplatelet Agents aspirin, cilostazol, clopidogrel, dipyridamole, prasugrel, ticlopidine Nonsteroidal Anti-Inflammatory Agents celecoxib, diclofenac, diflunisal, fenoprofen, ibuprofen, indomethacin, ketoprofen, ketorolac, mefenamic acid, naproxen, oxaprozin, piroxicam, sulindac Serotonin Reuptake Inhibitors citalopram, desvenlafaxine, duloxetine, escitalopram, fluoxetine, fluvoxamine, milnacipran, paroxetine, sertraline, venlafaxine, vilazodone

## 4. What approving would unlock in the live app

This section says what the code implies. It has not been run with a real approval.

- **FOOD-0001 approved alone (no grade needed):**
  - Its §5.5 chunk joins retrieval with a verified identity.
  - Any analysis that names lisinopril can then score it: lisinopril alone (R0, threshold 0.30), and pairs with lisinopril such as lisinopril + metformin (R2, threshold 0.60).
  - A chunk counts as related if it names any one requested drug.
  - Whether an answer is *released* still depends on the trust score, the LLM's cited claims and claim verification, so an abstention is still possible.
- **REL-LIVE-0003 or REL-LIVE-0004:**
  - Approving the manifest is **not enough**. With severity UNGRADED, the loader rejects the record. The record's evidence chunk is then not "cited", so it never joins retrieval.
  - Once graded and approved:
    - REL-LIVE-0003 adds lisinopril + spironolactone.
    - REL-LIVE-0004 adds warfarin + ibuprofen.
  - The grade also sets the risk tier: CONTRAINDICATED or MAJOR makes the pair R3, threshold 0.75.
  - The §7.3 chunk names about 40 drugs, so it would also be retrieved for other warfarin pairs (for example warfarin + sertraline). Only ibuprofen has a record; the pair-identity and claim checks decide what can be released.
- **Still abstains after all three:** simvastatin + clarithromycin, sertraline + omeprazole, metformin + amoxicillin, and every pair without a lisinopril or warfarin chunk.

## 5. Approval steps (from each manifest's `how_to_approve`)

1. **REL-LIVE-0003 and REL-LIVE-0004 only:** an authorized reviewer grades the severity with the project's documented method: one of CONTRAINDICATED, MAJOR, MODERATE, MINOR or NONE.
   - Edit only `severity` in `LIVE_RELATIONSHIP_RECORDS_V2.json`.
   - Recompute `records_sha256`. The hash is SHA-256 of the file with CRLF normalised to LF (`live_relationships._records_hash`).
2. Copy the three files of each dataset into its **own** folder:
   - `data/live_medical/relationships/v2/food_0001/`
   - `data/live_medical/relationships/v2/rel_live_0003/`
   - `data/live_medical/relationships/v2/rel_live_0004/`

   Never copy one dataset over another's files. The loader rejects a dataset that repeats a chunk or record ID that is already loaded.
3. In each manifest, set `"status": "APPROVED"` and `"approval": {"approved_by": "<name>", "approved_at": "<YYYY-MM-DD>"}`. Both fields are required (`_load_v2`).
4. `evidence_sha256` must still match: the evidence file is not edited.
5. Restart the backend. The startup log line "Relationship records: …" should name each dataset as approved.
6. Tests that check this path: `tests/e2e/test_live_evidence_provenance.py`, `tests/e2e/test_live_multi_dataset_loading.py`, `tests/e2e/test_live_warfarin_ibuprofen.py` and `tests/e2e/test_citation_alignment.py`. Run them, then the full suite (`TESTING=1`).

## 6. Who must approve

Earlier project notes set the rule:
- `reports/live_validation/REL_LIVE_0004_IBUPROFEN_REVIEW_PACKAGE_2026-10-24.md`;
- `CLAUDE_FEATURE_FINALIZATION_REPORT_2026-10-26.md`;
- `MEDICAL_RAG_ROUND2_ACCEPTANCE_2026-10-26.md`.

The rule they set: a severity grade must come from **an authorized clinician or pharmacist** using the documented grading method. Until then, the record stays UNGRADED.

- **REL-LIVE-0003 and REL-LIVE-0004:** this requirement applies. Both need a severity grade, a clinical judgement that the label does not give. Claude cannot supply it, and the owner should not guess it.
- **FOOD-0001:** needs no grade. Approving it is a research decision for the owner: confirm the text against DailyMed and accept the stated claim's limits. The project still asks for an authorized reviewer's name in `approved_by`.

## 7. Checklist for Sandeep: what to read on DailyMed

- [ ] Open https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=34ebeea1-6812-4697-84c4-b2ae4f39e55f. Confirm the title is LISINOPRIL TABLETS, and note the current SPL version (captured: v12).
- [ ] §5.5 Hyperkalemia reads as text 1 above. If the label has a newer version, decide whether to cite v12 or recapture.
- [ ] §7.1 Diuretics reads as text 2, and spironolactone is named among the potassium-sparing diuretics.
- [ ] Open https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=884cdbf6-0a52-4126-8e14-b0d7c9367e33. Confirm the title is WARFARIN SODIUM TABLETS, and note the version (captured: v8).
- [ ] §7.3 Drugs that Increase Bleeding Risk reads as text 3, and ibuprofen is in Table 3 under Nonsteroidal Anti-Inflammatory Agents.
- [ ] Confirm the RxCUIs on RxNav: lisinopril 29046, spironolactone 9997, warfarin 11289, ibuprofen 5640.
- [ ] Decide: approve FOOD-0001 now, or wait. For REL-LIVE-0003 and REL-LIVE-0004, arrange the clinician or pharmacist severity grading before any approval.
