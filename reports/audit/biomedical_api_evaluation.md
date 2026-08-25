# Biomedical API Candidate Evaluation Matrix

**Status:** `AUDITED & INTEGRATED`  
**Timestamp:** 2026-08-23T18:22:00Z  

---

## 1. Candidate Evaluation Matrix

| Source / Provider | Category | Purpose | Medical Relevance | Authority Tier | Provenance Level | Freshness | Rate Limit | License / Terms | Reproducible | Integration Decision |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **NCBI PubMed (E-utilities)** | Literature Discovery | Peer-reviewed article search, PMIDs, abstracts, MeSH terms | Critical (Peer-reviewed literature) | Tier 2 | High (Official NCBI) | Real-time / Daily | 3 req/sec (10 w/ Key) | Public Domain (US Govt) | Yes (Snapshot / PMID) | **INTEGRATE (P0)** |
| **Europe PMC REST API** | Literature Discovery | Open-access full text, PMIDs, PMCIDs, DOIs, grants | Critical (Open access text) | Tier 2 | High (EMBL-EBI) | Real-time / Daily | 10 req/sec | CC BY / Open Access | Yes (Snapshot / DOI) | **INTEGRATE (P0)** |
| **NLM RxNorm / RxNav** | Drug Normalization | RxCUI resolution, brand/generic mapping | Critical (Drug entity grounding) | Tier 2 | High (NLM) | Weekly / Monthly | 20 req/sec | Public Domain (NLM) | Yes (RxCUI versioned) | **INTEGRATE (P0)** |
| **openFDA Drug Labeling** | Regulatory Safety | FDA drug package inserts, black box warnings, ADEs | High (FDA regulatory labels) | Tier 1 | High (FDA) | Weekly updates | 240 req/min | Public Domain (FDA) | Yes (Snapshot) | **INTEGRATE (P0)** |
| **ClinicalTrials.gov API** | Clinical Registries | Trial status, interventions, study design, NCT IDs | High (Clinical trial status) | Tier 1 | High (NIH) | Weekday updates | 10 req/sec | Public Domain (NIH) | Yes (NCT ID) | **INTEGRATE (P1)** |
| **Crossref DOI API** | Scholarly Metadata | DOI metadata verification, publication dates, journal info | Medium (Metadata resolution) | Tier 3 | High (Crossref) | Real-time | 50 req/sec | Open Data (CC0) | Yes (DOI) | **INTEGRATE (P1)** |
| **Semantic Scholar API** | Academic Graph | Citation graph, related papers, author metadata | Medium (Graph expansion) | Tier 3 | Medium (AI2) | Daily | 100 req/5min | Open Access / AI2 | Yes (Paper ID) | **OPTIONAL (P2)** |
| **OpenAlex API** | Scholarly Graph | Disambiguation, journal metadata, institution graph | Medium (Entity expansion) | Tier 3 | Medium (OurResearch) | Weekly | 10 req/sec | CC0 Open Data | Yes (Work ID) | **OPTIONAL (P2)** |

---

## 2. Summary of Integration Choices

- **P0 Priority (Implemented):** NCBI PubMed, Europe PMC, NLM RxNorm, and openFDA form the core Biomedical Evidence Source Layer.
- **P1 Priority (Supported):** ClinicalTrials.gov and Crossref provide clinical trial registration status and DOI metadata verification.
- **P2 Priority (Discovery Catalogue):** Semantic Scholar and OpenAlex are evaluated as discovery catalogues via the `public-apis` discovery list and do not form core runtime dependencies.
