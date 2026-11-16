# Nutrition source audit, pass 2, and permission-request drafts (2026-10-28)

Read-only. **Nothing was connected, ingested, approved or sent.** No request has gone to any publisher, and no permission is claimed. FOOD-CANDIDATE-1, the live corpus and FOOD-0001 are unchanged. Owner decisions N1–N7 (2026-10-28) govern this pass.

## 0. Bottom line

- **The Indian clinical sources found** are ICMR Standard Treatment Workflows (CKD), the ICMR 2018 Type 2 Diabetes guideline, RSSDI 2022 and the RSSDI 2025 nutrition guideline (supported by ICMR–NIN).
  - **Fit:** they are the closest match to an Indian condition-diet use case.
  - **Permission:** none states a reuse licence that I could verify, so all are **LICENCE_UNCLEAR** or **WRITTEN_PERMISSION_REQUIRED**.
- **Hospital and clinic sites:** Mayo Clinic's reprint page and a Fortis blog returned 403 to automated reading, which itself signals restricted automated access. These are discovery leads only.
- **NIDDK contact (N2):** NIDDK's contact page says its Health Information Center "is not providing inquiry response services" during restructuring and points to nih.gov. N2 therefore has **no confirmed contact route**. The draft below is addressed through the NIDDK copyright page's contact link or nih.gov, and may go unanswered.
- **Recommended evidence sources:** none changes from pass 1. Mode B stays `NO_APPROVED_EVIDENCE` (N1).

## 1. Additional sources (pass 2)

How verified: "search" = official URL found through search results, but the text was not read in full; "fetched" = the page was opened.

| Source | Publisher / date | Class | What it contains (as found) | Reuse | Fit | Questions for the publisher |
|---|---|---|---|---|---|---|
| ICMR Standard Treatment Workflow: Chronic Kidney Disease | ICMR; PDF file dated 13 Jul 2026; an older version also exists | CONDITION_DIET candidate (clinician workflow) | Via search: salt < 5 g/day; protein 0.8 g/kg/day (the older version says 0.6–0.8, so the versions **conflict**); restrict potassium and salt substitutes when hyperkalemia is present; the older version lists low-potassium foods | **LICENCE_UNCLEAR.** No licence on the ICMR pages found. The fetched PDF is a graphic, so its text could not be read automatically. | High for India (CKD); written for clinicians, not patients | Can selected passages be stored and shown with attribution in a research prototype? Which version is current? |
| ICMR Guidelines for Management of Type 2 Diabetes 2018 (§6.2 Medical Nutrition Therapy) | ICMR, 2018 | CONDITION_DIET candidate | MNT section exists (p. 16); content seen only through secondary reviews | **LICENCE_UNCLEAR** | Medium–high; dated 2018 | Is there a current edition? What are the reuse terms? |
| RSSDI 2025 Nutrition Guidelines for Individuals with T2D (supported by ICMR–NIN) | RSSDI, 2025 (PDF hosted by a third party, cmeindia.in) | CONDITION_DIET candidate | Current Indian diabetes nutrition guidance (not read in full) | **WRITTEN_PERMISSION_REQUIRED** (society copyright; the official host is not confirmed) | High for India (diabetes) | Official source URL; permission for storage and display |
| RSSDI Clinical Practice Recommendations 2022 | RSSDI; Int J Diabetes Dev Ctries, Suppl 1 | CONDITION_DIET candidate | Nutrition chapter (not read) | **WRITTEN_PERMISSION_REQUIRED** (© RSSDI) | Medium | Same |
| ADA Standards of Care in Diabetes 2026 | American Diabetes Association, Dec 2025 ("living" standard, updated during the year) | CONDITION_DIET candidate | Nutrition section updated for 2026 | **LICENCE_UNCLEAR** (journal or ADA permissions not found); some materials are paid | Medium (US-centred; versions change during the year) | Permissions through Diabetes Care |
| KDIGO 2024 CKD | KDIGO / Kidney International | CONDITION_DIET candidate | Graded statements (from pass 1, secondary) | **LICENCE_UNCLEAR** | High (CKD) | Article licence |
| Indian Society of Nephrology CKD diet guidance | ISN | — | Not found in this pass | — | — | Locate the official guidance |
| Mayo Clinic, Cleveland Clinic | Hospitals | GENERAL_NUTRITION / discovery | Both have reprint and licensing pages (search results); Mayo's page returned 403 when fetched | **WRITTEN_PERMISSION_REQUIRED** (both run licensing programmes) | Discovery only | — |
| Fortis Healthcare blog (CKD diet; clinician author) | Hospital blog | Discovery | Returned 403; search snippet: warns against cutting protein without advice | Not assessed | Discovery only; trace every claim to a guideline | — |
| Recipe and wellness sites (e.g. CKD recipe collections) | Commercial | Discovery | Recipes; not medical evidence | Not assessed | **Not suitable** as evidence | — |
| PMC review "A roadmap to medical nutrition therapy in T2D" | Journal (PMC) | RESEARCH_EVIDENCE | Reviews ICMR, RSSDI and other MNT guidance | Article-level licence (check per article) | Discovery and appraisal (N6) | — |

**Not covered in pass 2:**
- Indian Dietetic Association statements;
- AIIMS and other university dietetics pages;
- non-English (Hindi and regional) sources;
- recommendation-level evidence grades.

Covering these needs targeted reading of each publisher's pages, and several block automated access.

## 2. Evidence-reuse recommendations

1. **For a first approved CONDITION_DIET record, prefer one Indian clinical source with written permission:** an ICMR STW (CKD) or RSSDI 2025 (diabetes). A record should hold:
   - the exact passage;
   - the version and date;
   - the condition and population;
   - the qualifier (for example, "when hyperkalemia is present");
   - the direction, reviewed by a named person;
   - the permission reference.
2. **Resolve version conflicts before any record exists.** The ICMR CKD workflow versions differ on protein (0.6–0.8 vs 0.8 g/kg/day). Pin one version by hash.
3. **Keep food lists such as "low-potassium fruits" as CONDITION_DIET only when the guideline itself states them for the condition.** Never derive them from composition data (N4).
4. **Treat PubMed and Europe PMC as discovery only (N6).** Open Food Facts stays rejected (N5).

## 3. Permission tracker

| # | Publisher | Material | Requested uses | Contact route (to verify) | Status |
|---|---|---|---|---|---|
| P1 | NIDDK (NIH) | Specific condition-eating pages (CKD, diabetes) | Store passages; index; display exact wording beside a confirmed condition; derived records with links | NIDDK copyright page → "contact NIDDK"; the Health Information Center says inquiries are paused; fallback: nih.gov | **Draft ready; not sent.** Contact route uncertain. |
| P2 | ICMR–NIN | Dietary Guidelines for Indians 2024 | Same | ICMR–NIN director's office, via the official nin.res.in contact page (verify the address there; addresses seen only in third-party listings are not used) | **Draft ready; not sent** |
| P3 | ICMR–NIN | Indian Food Composition Tables 2017 | Pinned facts for an approved record only | Same as P2 | **Draft ready; not sent** |
| P4 | ICMR (HQ) | Standard Treatment Workflows (CKD and others) | Same as P1 | icmr.gov.in contact page | Not drafted (optional; owner to decide) |
| P5 | RSSDI | 2025 Nutrition Guidelines | Same as P1 | RSSDI official site | Not drafted (optional) |

## 4. Draft request to NIDDK (for the owner to send; not sent)

> **Subject:** Permission and clarification: use of NIDDK health information pages in a non-commercial research prototype
>
> Dear NIDDK Communications team,
>
> I am a postgraduate researcher (M.Tech) building a non-commercial research prototype, the "Adaptive Trust-Aware Medical RAG". It is a system that answers medication questions only from verified, cited evidence and abstains when evidence is insufficient. It is not deployed to patients and is not a clinical tool.
>
> Your copyright page (last reviewed May 2024) says most NIDDK content is copyright-free and may be reproduced with credit. It also says content may not be used "to recommend specific medical advice, treatments, or referrals." I would like to confirm whether the following uses are acceptable for specific pages, such as "Healthy Eating for Adults with Chronic Kidney Disease":
>
> 1. Storing selected passages, unchanged, in a local research database, with the page URL, retrieval date and NIDDK attribution.
> 2. Indexing those passages for retrieval inside the prototype.
> 3. Displaying the exact passage, credited to NIDDK and linked to the page, to a research user who has entered a confirmed health condition (e.g. CKD). The display would carry a disclaimer that it is educational information and not personal medical advice.
> 4. Creating structured records that reference the passage: condition, population, qualifiers and source link. No wording would be changed, and nothing would imply NIDDK endorsement. NIDDK logos would not be used.
> 5. Removing or updating stored passages whenever NIDDK revises or withdraws a page.
>
> Would item 3 fall under the restriction on recommending specific medical advice? If so, is there a form of display (for example, link-only or embedded content) that NIDDK would accept? Any future deployment beyond research would be raised with you separately.
>
> Thank you,
> [Owner name, affiliation, contact]

## 5. Draft request to ICMR–NIN (for the owner to send; not sent)

> **Subject:** Request for written permission: research use of Dietary Guidelines for Indians (2024) and Indian Food Composition Tables (2017)
>
> Dear Director, ICMR–National Institute of Nutrition,
>
> I am a postgraduate researcher (M.Tech) developing a non-commercial research prototype, the "Adaptive Trust-Aware Medical RAG". It answers medication-related questions only from verified, cited evidence and abstains when evidence is insufficient. It is not a clinical product and is not deployed to patients.
>
> The 2024 Dietary Guidelines for Indians state that the material may not be stored or reproduced electronically to create a product without written permission from NIN. I request written permission for the following, separately for each publication:
>
> **A. Dietary Guidelines for Indians, 2024**
> 1. Storing selected passages, unchanged, in a local research database, with full citation (ICMR–NIN Expert Committee, 2024), page numbers and the retrieval date.
> 2. Indexing those passages for retrieval within the prototype.
> 3. Displaying the exact passage, with attribution, to a research user alongside a confirmed health condition or dietary instruction, with a disclaimer that it is not personal medical advice.
> 4. Creating structured records that reference each passage: topic, population, qualifiers and page. NIN's wording would not be changed.
>
> **B. Indian Food Composition Tables, 2017**
> 1. Storing selected nutrient values for specific foods as reference facts, with table and page citations. They would only be used to describe a food named in an approved guidance record, and never to generate dietary advice on their own.
>
> For both, I would remove or update stored content on request or when NIN publishes revisions. I would display NIN attribution as you specify, and seek separate permission before any use beyond non-commercial research. Please let me know of any conditions, required wording or fees.
>
> Thank you,
> [Owner name, affiliation, contact]

## 6. Open licensing questions

1. Does NIDDK consider displaying stored wording beside a user's condition to be "recommending specific medical advice"?
2. Do ICMR STWs carry any reuse licence? Which CKD version is current?
3. Who holds the rights to RSSDI 2025, and where is its official URL?
4. What are the reuse terms of the KDIGO 2024 and ADA 2026 articles?
5. What licence does the Canadian Nutrient File carry (open.canada.ca), and what are the 2025–2030 DGA terms? Both are low priority.

## 7. Verdicts (separate)

| Area | Status |
|---|---|
| Nutrition-source suitability | Candidates identified; **none approved**; every condition-diet source needs permission or licence clarification |
| Food-feature readiness | Unchanged: FOOD-CANDIDATE-1 implemented in its own copy; Mode B is `NO_APPROVED_EVIDENCE` |
| Clinical validation | Absent |
