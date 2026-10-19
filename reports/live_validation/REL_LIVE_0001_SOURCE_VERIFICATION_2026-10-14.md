# REL-LIVE-0001 source verification

**Date:** 2026-10-14
**Record:** REL-LIVE-0001 in `data/live_medical/relationships/LIVE_RELATIONSHIP_RECORDS_V1.json` (simvastatin RxCUI 36567, CONTRAINDICATION, clarithromycin RxCUI 21212, A_TO_B, CONTRAINDICATED, source chunk `DAILYMED-SPL-SIMVASTATIN-001-CHUNK-01`)
**Researcher decision:** verify first; do not approve until the source and medication identities are verified.
**Outcome:** the relationship is supported by two current DailyMed labels and both RxCUIs resolve to the expected ingredients. The record's source chunk, however, is not a verbatim excerpt of any label checked and carries a placeholder URL. **REL-LIVE-0001 stays `CANDIDATE_PENDING_RESEARCHER_APPROVAL`, and approving it is not recommended.** A V2 candidate should be built from byte-exact label text.

## 1. How the sources were read

- **Direct downloads failed.** The cloud environment and the device VM both tried to fetch `dailymed.nlm.nih.gov`, `rxnav.nlm.nih.gov` and `api.fda.gov` directly. The network policy refused every request (proxy 403 on CONNECT).
- **Web reader instead.** The label pages and RxNav records were read through Claude's web reader. This reader converts the page and answers through a small model, and it quotes at most about 110 characters at a time.
- **What this means for the quotes.** The quotes below are what the reader returned. They are **not byte-exact copies**. Whitespace, case and cross-reference markup may differ from the SPL source.
- **Next step.** `scripts/capture_live_relationship_sources.py` downloads the same documents byte for byte on a machine that can reach them.

## 2. Medication identities (RxNav)

| RxCUI | URL read | Name | Term type | Suppressed |
|---|---|---|---|---|
| 36567 | https://rxnav.nlm.nih.gov/REST/rxcui/36567/properties.json | simvastatin | IN (ingredient) | N |
| 21212 | https://rxnav.nlm.nih.gov/REST/rxcui/21212/properties.json | clarithromycin | IN (ingredient) | N |

Both are distinct ingredient-level concepts, which is the level the live normaliser maps to. The values were returned by the RxNav REST endpoint through the web reader. They still need a byte-exact capture, which the capture script performs.

## 3. Prescribing information

### Simvastatin (innovator label)

- **Label:** "ZOCOR- simvastatin tablet, film coated", Organon LLC. Set ID `8f55d5de-5a4f-4a39-8c84-c53976dd6af9`. Revised 8/2023; DailyMed shows "Updated March 28, 2025". The version number was not shown on the page.
- **URL:** https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=8f55d5de-5a4f-4a39-8c84-c53976dd6af9
- **Section 4, first contraindication (as read):** "Concomitant use of strong CYP3A4 inhibitors (select azole anti-fungals, macrolide antibiotics, anti-viral medications, and nefazodone)". Clarithromycin is not named in section 4 itself.
- **Section 7, Table 2, "Strong CYP3A4 inhibitors" row (as read):**
  - Intervention: "Concomitant use of strong CYP3A4 inhibitors with ZOCOR is contraindicated" … "If treatment with a CYP3A4 inhibitor is unavoidable, suspend ZOCOR during the course of strong CYP3A4 inhibitor treatment."
  - Examples: "… select macrolide antibiotics (e.g., erythromycin and clarithromycin), …"
- **What this label supports:** the contraindication is stated for the class (strong CYP3A4 inhibitors), and clarithromycin is named as a member of that class. No single sentence in this label names both "simvastatin" and "clarithromycin". The drug is called ZOCOR in the table.

### Clarithromycin

- **Label:** "CLARITHROMYCIN tablet, film coated", Aurobindo Pharma Limited. Set ID `9aaffb41-408c-4372-8fd5-1d649450c0e9`. Revised 10/2023; DailyMed shows "Updated October 10, 2023".
- **URL:** https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=9aaffb41-408c-4372-8fd5-1d649450c0e9
- **Section 4.5 "Lomitapide, Lovastatin, and Simvastatin" (as read):** "Concomitant administration of clarithromycin tablets with HMG-CoA reductase inhibitors (statins) that are extensively metabolized by CYP3A4 (lovastatin or simvastatin) is contraindicated due to the increased risk of myopathy, including rhabdomyolysis [see Warnings and Precautions (5.4) and Drug Interactions (7)]."
- **What this label supports:** this one sentence names both medications and states the contraindication. It is the best single evidence span for the record.

### Also seen (not proposed as the source)

- **Label:** a repackager's simvastatin label (Proficient Rx LP, set ID `7649bec7-04c6-47b5-a050-15923006dac0`, Revised 4/2022). It still carries the older wording.
- **Section 4 (as read):** "Concomitant administration of strong CYP3A4 inhibitors (e.g., itraconazole, ketoconazole, posaconazole, voriconazole, HIV protease inhibitors, boceprevir, telaprevir, erythromycin, clarithromycin, telithromycin, nefazodone, and cobicistat-containing products) [see WARNINGS AND PRECAUTIONS (5.1)] ."
- **Section 5.1 (as read):** "… the macrolide antibiotics erythromycin and clarithromycin, … Combination of these drugs with simvastatin is contraindicated."

## 4. The frozen corpus chunk

`DAILYMED-SPL-SIMVASTATIN-001-CHUNK-01` (content hash `8ed70a5c8466c80e49ff874c8e7c11bb0b99917a02dbc455a39e7119c072c1d5`, `document_url` `https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=example-simvastatin`) reads:

> Simvastatin is a cholesterol-lowering medication. CONTRAINDICATIONS: Concomitant administration of strong CYP3A4 inhibitors (e.g., itraconazole, ketoconazole, posaconazole, voriconazole, HIV protease inhibitors, boceprevir, telaprevir, erythromycin, clarithromycin, telithromycin) is contraindicated due to increased risk of myopathy and rhabdomyolysis.

Compared with the older simvastatin wording, the chunk:
- drops "nefazodone, and cobicistat-containing products" and the cross-reference;
- ends with "is contraindicated due to increased risk of myopathy and rhabdomyolysis", which is close to the clarithromycin label's wording.

An exact-phrase web search found no document containing the chunk's sentence. The chunk agrees with the labels in content, but it is not a verbatim excerpt of any label checked. With a placeholder URL, its provenance cannot be linked to an authoritative document. Following the decision, the frozen corpus was **not** edited.

## 5. Checks required before approval

| Check | Result |
|---|---|
| Both RxCUIs are valid, distinct, canonical entities | Yes, through the web reader (IN, not suppressed). Byte-exact capture pending |
| Predicate grounded in source wording | Yes: "is contraindicated" (clarithromycin 4.5) and "Concomitant use of strong CYP3A4 inhibitors with ZOCOR is contraindicated" (simvastatin Table 2) |
| Direction grounded in source wording | Both labels contraindicate taking the two drugs together, so the contraindication holds in both orders. **BIDIRECTIONAL** fits the sources; V1 records A_TO_B |
| Severity consistent with the source | Yes: CONTRAINDICATED in both labels |
| Source chunk and content hash match the manifest | Yes for V1 against the frozen chunk, but the chunk itself is not label text |
| Evidence span verbatim in the source | **No.** V1's span is the frozen chunk text, which is not verbatim in any label checked |
| Source URL real and matches the evidence | **No.** V1's chunk URL is a placeholder |
| Candidate hash independently reproducible | Yes. Records file `b4d06362e2d21edbf43826ec7aa79a3282946a025521a50ee6d41d5b9314d277` (CRLF normalised to LF), manifest `09e131823555e323d10697ee122745f94cc678ae1f293ad8c0040855adbeeb71` |

Two checks fail, so REL-LIVE-0001 stays `CANDIDATE_PENDING_RESEARCHER_APPROVAL`. Its manifest now records these findings under `verification_2026_10_14`. The running application loads no relationship records, and the pair stays at R2.

### Wording the record must keep

- The labels state a **contraindication** of taking the two drugs together. That is narrower and stronger than "interacts with".
- The mechanism is directional: clarithromycin inhibits CYP3A4, which raises simvastatin exposure. The record does not state the mechanism, and a mechanism claim needs its own record.

## 6. Path to an approvable candidate (V2)

1. **Capture.** On your machine, run `python scripts/capture_live_relationship_sources.py`. It saves both SPL XML documents, their version histories and both RxNav records to `data/live_medical/relationships/source_capture/<date>/`, together with a manifest of URLs, sizes and SHA-256 hashes. The folder is ignored by git.
2. **Build V2 from the captured bytes (Claude).**
   - A new versioned candidate evidence chunk holding the verbatim clarithromycin section 4.5 sentence, and optionally the ZOCOR Table 2 row. It carries the real URL, set ID, SPL version and effective date, and its recomputed content hash.
   - `LIVE_RELATIONSHIP_RECORDS_V2`: CONTRAINDICATION, BIDIRECTIONAL, CONTRAINDICATED, grounded in that chunk.
   - A manifest recording the provenance.
   - The frozen `LIVE_MEDICAL_CORPUS_V2` stays unchanged.
3. **Embed.** Compute the candidate chunk's embedding with the pinned all-MiniLM-L6-v2 on your machine, since the model cannot be downloaded in the cloud.
4. **Decide.** You review V2 and approve, amend or reject it. Only after that would the application be changed to load the approved candidate chunk. Nothing is added to the running application before then.

## Sources read

- [ZOCOR (simvastatin), Organon, DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=8f55d5de-5a4f-4a39-8c84-c53976dd6af9)
- [Clarithromycin, Aurobindo, DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=9aaffb41-408c-4372-8fd5-1d649450c0e9)
- [Simvastatin, Proficient Rx, DailyMed](https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=7649bec7-04c6-47b5-a050-15923006dac0)
- [Clarithromycin, RedPharm, DailyMed](https://dailymed.nlm.nih.gov/dailymed/lookup.cfm?setid=5047246b-310f-5ae0-e054-00144ff8d46c) (older 2016 text, same 4.5 contraindication)
- [RxNav properties for 36567](https://rxnav.nlm.nih.gov/REST/rxcui/36567/properties.json) and [21212](https://rxnav.nlm.nih.gov/REST/rxcui/21212/properties.json)
