# Nutrition source and API audit, first pass (2026-10-28)

Read-only research for the future patient-food stage (FOOD-CANDIDATE-1). **No source has been connected, downloaded into the project, ingested or approved.** No application code, schema, report or research artifact was changed for this audit. This is a source-suitability and permissions review, not clinical advice.

## 0. Bottom line

- **No single source** gives approved, patient-specific, condition-to-food recommendations with reuse rights for an electronic product. The owner's three-layer design is the right one:
  - **CONDITION_DIET:** the only layer that may authorise advice;
  - **FOOD_COMPOSITION:** facts only;
  - **RESEARCH_EVIDENCE:** discovery only.

  MEDICATION_FOOD stays in the medication branch, and GENERAL_NUTRITION is never personalised.
- **Nothing can be approved for CONDITION_DIET today.** Every guideline-grade candidate has a reuse condition that blocks a copied evidence store without the publisher's agreement:
  - **NIDDK:** forbids using its content "to recommend specific medical advice".
  - **ICMR–NIN 2024:** electronic storage for a product needs written permission.
  - **NICE outside the UK:** needs a signed licence.
  - **WHO:** non-commercial only, with share-alike.
- **The cleanest technical sources are fact sources, not recommendation sources:**
  - **USDA FoodData Central:** CC0.
  - **openFDA:** CC0, with exceptions.
  - **DailyMed** web services.
- **FOOD-CANDIDATE-1 should keep returning `NO_APPROVED_EVIDENCE`** in Mode B until the owner obtains a permission (section 5) and named reviewers approve individual records.

## 1. Method and coverage

- **Searches and fetches:** web searches and fetches on 2026-10-28 from this PC, in English only, focused on India, the US, the UK, Canada, the EU and global sources.
- **Primary pages read directly:**
  - NIDDK copyright;
  - USDA FDC API guide;
  - WHO copyright and licensing;
  - PMC copyright;
  - the Canadian Nutrient File about page;
  - Open Food Facts terms of use;
  - openFDA terms;
  - DailyMed web services.
- **Search results only** (official pages listed in results, but not opened, or blocked):
  - NICE reuse pages: the page returned 403;
  - ICMR–NIN Dietary Guidelines 2024: the PDF returned 404 at the fetched path, and the snippet was garbled;
  - IFCT 2017;
  - KDIGO 2024: secondary summaries only;
  - Dietary Guidelines for Americans 2025–2030;
  - EFSA.
- **Not reachable:** NIH ODS copyright (403) and Europe PMC copyright (403).
- **Not covered yet:**
  - hospital, university and professional-society sites (ADA, KDOQI, Indian professional bodies);
  - blogs and commercial nutrition sites;
  - non-English sources;
  - the evidence grades of individual recommendations.

This is a first pass, not a complete survey. Each "unresolved" item below needs the publisher's page read in full, or a written answer from the publisher.

## 2. Source register

Legend for permission: **VERIFIED** = REUSE_PERMISSION_VERIFIED, **CONDITIONAL** = REUSE_PERMISSION_CONDITIONAL, **WRITTEN** = WRITTEN_PERMISSION_REQUIRED, **UNCLEAR** = LICENCE_UNCLEAR.

| Source | Evidence class | What it can support | Access | Reuse classification (how verified) | Fit for the patient-food stage |
|---|---|---|---|---|---|
| **NIDDK** health information (e.g. eating with CKD) | CONDITION_DIET candidate | Plain-language, condition-specific dietary education (CKD, diabetes) | Web pages; NIDDK prefers linking or embedding ("we update content regularly") | **CONDITIONAL, with a blocking clause** (primary page, last reviewed May 2024). Most content is "copyright free". Credit NIDDK if unchanged; drop logos if edited; third-party graphics are restricted; content must not be used "to recommend specific medical advice, treatments, or referrals". | **Blocked for record-level recommendations** until NIDDK confirms that this use is allowed. Strong candidate otherwise. |
| **ICMR–NIN Dietary Guidelines for Indians 2024** | GENERAL_NUTRITION; some condition advice | Indian dietary patterns; general and some NCD guidance | PDF | **WRITTEN** (search snippet of the copyright notice: no electronic storage or reproduction to create a product without NIN's written permission). Read the full notice before relying on it. | High relevance for India; needs written permission from NIN |
| **ICMR–NIN Indian Food Composition Tables 2017** | FOOD_COMPOSITION | Nutrients of Indian foods | PDF book; third-party digitisations exist (not official) | **UNCLEAR** (snippet: © 2017 NIN, with a no-warranty disclaimer; no licence found) | Best Indian food-fact source; ask NIN about a licence |
| **NICE** guidelines (e.g. CKD) | CONDITION_DIET candidate | Guideline-grade recommendations with stated scope | Web; syndication API with licence | **WRITTEN** for use outside the UK (search results from nice.org.uk: international use needs written permission and a signed licence; syndication and AI use carry fees outside the UK; the UK Open Content Licence covers UK use only) | Strong evidence, but a licence and fee are likely for India |
| **KDIGO 2024 CKD guideline** | CONDITION_DIET candidate | Graded CKD nutrition statements (e.g. protein 0.8 g/kg/day, sodium <2 g/day; secondary summaries) | Journal article (Kidney International) | **UNCLEAR** (licence not found) | Strong clinical source; licence and exact wording must come from the article |
| **WHO** healthy diet and publications | GENERAL_NUTRITION | Population-level healthy-diet principles | Web, PDF | **CONDITIONAL** (primary page): CC BY-NC-SA 3.0 IGO for publications; commercial use needs permission; adaptations must keep similar terms and a disclaimer; third-party figures need separate permission; the website-content licence is not stated on that page | Background only; not patient-specific |
| **Dietary Guidelines for Americans 2025–2030** | GENERAL_NUTRITION | US population guidance | realfood.gov | **UNCLEAR** for 2025–2030. The 2020–2025 materials were public domain, but most photos and illustrations were not, and altered content must not cite the DGA. | Background only; US-centred |
| **NIH Office of Dietary Supplements** | GENERAL_NUTRITION, nutrient-drug notes | Vitamins, minerals, supplements, some interactions | Web fact sheets | **UNCLEAR** (copyright page returned 403) | Supplement questions only |
| **USDA FoodData Central** | FOOD_COMPOSITION | Measured nutrients; stable FDC IDs | REST API (`/fdc/v1`, data.gov key, 1,000 requests/hour per IP; DEMO_KEY 30/hour) and bulk downloads; versioned releases | **VERIFIED** (primary page): CC0 1.0, "not copyrighted"; credit requested | Good fact source with pinned offline snapshots; never authorises advice. US foods; weak for Indian dishes. |
| **Canadian Nutrient File 2026** | FOOD_COMPOSITION | 5,993 foods, up to 173 nutrients | CSV download; no API mentioned | **UNCLEAR** (the about page names no licence; it links to open.canada.ca, which was not read) | Optional supplement |
| **EFSA food composition** | FOOD_COMPOSITION | EU foods; an open EU FCDB is expected mid-2026 (search result) | — | **UNCLEAR** | Low priority for India |
| **FAO/INFOODS** | Directory | Finding national databases | Web | Not reviewed in detail | Discovery only |
| **Open Food Facts** | FOOD_COMPOSITION (packaged products) | Ingredients and label nutrients | API and dumps | **CONDITIONAL** (primary page): database ODbL, contents DbCL, images CC BY-SA 3.0; share-alike; and "must not be used for medical purposes" | **Not suitable** for any medical use, by its own terms |
| **PubMed / PMC** | RESEARCH_EVIDENCE | Discovery and metadata | E-utilities; PMC OAI-PMH, FTP and Cloud only for bulk | **CONDITIONAL** (primary page): copyright applies unless the licence says otherwise; bulk download from the PMC site is "prohibited"; reuse depends on each article's licence | Discovery layer; every claim needs appraisal and an article-level licence check |
| **Europe PMC** | RESEARCH_EVIDENCE | Search and open-access full text | REST API | **UNCLEAR** (copyright page returned 403) | Discovery layer |
| **DailyMed** | MEDICATION_FOOD | Label text, set IDs, version history | REST v2, GET only, HTTPS | Copyright page not read; label text is generally reused in the existing branch | Keep in the medication branch only |
| **openFDA** | MEDICATION_FOOD (labels, events) | Structured label fields | API | **VERIFIED** (primary page): mostly CC0, with exceptions for third-party content (e.g. GMDN) | Possible complement to DailyMed; never condition-diet |

## 3. What each class may and may not do

- **FOOD_COMPOSITION** (USDA, IFCT, CNF, Open Food Facts) can state "food X contains N mg potassium per 100 g". It can never decide that a patient should eat or avoid X.
- **MEDICATION_FOOD** (DailyMed, openFDA) supports drug-food warnings in the existing medication branch. It must not become condition-diet advice.
- **RESEARCH_EVIDENCE** (PubMed, PMC, Europe PMC) finds studies. A finding becomes a CONDITION_DIET record only after appraisal (design, population, outcomes, conflicts) and a reuse check, and with owner approval.
- **GENERAL_NUTRITION** (WHO, DGA, NIN guidelines) is not personalised advice for a diagnosed condition.
- **CONDITION_DIET** needs every one of these:
  - an exact passage that states the dietary action for the condition and population;
  - the qualifiers;
  - a reuse permission that covers storing the wording;
  - a named reviewer;
  - an approved direction.

## 4. Ranking for the first CONDITION_DIET records (by the owner's criteria)

1. **NIDDK CKD and diabetes eating pages.** These are explicit, condition-specific, current (reviewed 2024) and mostly copyright-free. **Blocked** by the "specific medical advice" clause until NIDDK confirms the use.
2. **ICMR–NIN 2024**, for the Indian context. This needs written permission, and its condition-specific coverage must be checked passage by passage.
3. **KDIGO 2024 (CKD).** These are graded recommendations, but the licence and the exact text must come from the article.
4. **NICE (CKD and others).** Guideline-grade, but an international licence and fee are likely.

## 5. Decisions for the owner

| # | Decision | Recommended |
|---|---|---|
| N1 | Keep Mode B at `NO_APPROVED_EVIDENCE` until a permission exists | Yes |
| N2 | Ask NIDDK whether storing exact page wording, and showing it beside a patient's confirmed condition in a research prototype, falls under "recommend specific medical advice" | Yes, first |
| N3 | Ask ICMR–NIN for written permission (Dietary Guidelines 2024 and IFCT 2017) for a research prototype | Yes, for the Indian context |
| N4 | Allow USDA FDC as a pinned offline FOOD_COMPOSITION snapshot (facts only, never advice) | Defer until a CONDITION_DIET record needs a food fact |
| N5 | Reject Open Food Facts for any medical use (its own terms) | Yes |
| N6 | Use PubMed / Europe PMC only for discovery, with no automated bulk copying | Yes |
| N7 | Complete the uncovered categories (professional societies, hospital and university sites, blogs) in a second pass | Owner's choice |

Nothing above is approved. Each "yes" is a recommendation for the owner's decision.

## Sources consulted

- [NIDDK copyright](https://www.niddk.nih.gov/copyright)
- [USDA FoodData Central API guide](https://fdc.nal.usda.gov/api-guide/)
- [WHO copyright and licensing](https://www.who.int/about/policies/publishing/copyright)
- [PMC copyright notice](https://pmc.ncbi.nlm.nih.gov/about/copyright/)
- [Canadian Nutrient File, about](https://www.canada.ca/en/health-canada/services/food-nutrition/healthy-eating/nutrient-data/canadian-nutrient-file-about-us.html)
- [Open Food Facts terms of use](https://world.openfoodfacts.org/terms-of-use)
- [openFDA terms](https://open.fda.gov/terms/)
- [DailyMed web services](https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm)
- [NICE reusing our content](https://www.nice.org.uk/re-using-our-content) (search result; the page returned 403)
- [NICE syndication API](https://www.nice.org.uk/about/what-we-do/nice-syndication-api)
- [NICE content for AI purposes](https://www.nice.org.uk/reusing-our-content/use-of-our-content-for-ai-purposes)
- [ICMR–NIN Dietary Guidelines for Indians 2024 (PDF)](https://www.nin.res.in/dietaryguidelines/pdfjs/locale/DGI24thJune2024fin.pdf) (search snippet)
- [IFCT 2017 (PDF)](https://nin.res.in/ebooks/IFCT2017.pdf)
- [Indian Nutrient Databank study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11277795)
- [NephJC on KDIGO 2024 CKD](https://www.nephjc.com/news/kdigo-ckd-part2) (secondary)
- [ODPHP: Dietary Guidelines 2025–2030](https://odphp.health.gov/healthypeople/tools-action/browse-evidence-based-resources/dietary-guidelines-americans-2025-2030)
- [EFSA food composition](https://www.efsa.europa.eu/en/data-report/food-composition)
