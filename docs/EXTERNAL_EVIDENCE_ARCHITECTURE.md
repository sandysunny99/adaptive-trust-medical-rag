# External Evidence Source Layer Architecture

**Specification Version:** `1.0.0`  
**Project:** Adaptive Trust-Aware Medical RAG  
**Component:** Evidence Source Layer (`src/adaptive_trust_medical_rag/evidence_sources/`)  

---

## 1. Executive Summary

The **Evidence Source Layer** establishes a controlled, decoupled interface for acquiring external medical evidence, peer-reviewed literature, publication metadata, RxNorm drug concept normalization, openFDA drug safety labeling, source provenance tracking, and reproducible snapshot replay.

---

## 2. Evidence Source Hierarchy & Classification

External evidence providers are categorized into structured authority tiers:

| Authority Tier | Source Type Identifier | Provider / System Examples | Primary Use Case & Claim Fit |
| :--- | :--- | :--- | :--- |
| **Tier 1** | `PRIMARY_REGULATORY` | openFDA (`openfda`) | FDA approved drug labels, black box warnings, adverse events (`claim_source_fit: fda_labeling`). |
| **Tier 1** | `PRIMARY_CLINICAL_REGISTRY` | ClinicalTrials.gov (`clinicaltrials`) | Trial registration status, study design, recruitment (`claim_source_fit: trial_status`). |
| **Tier 2** | `ENTITY_TERMINOLOGY` | NLM RxNorm (`rxnorm`) | Drug CUI resolution, brand-to-generic concept mapping (`claim_source_fit: drug_normalization`). |
| **Tier 2** | `BIOMEDICAL_LITERATURE` | NCBI PubMed (`pubmed`), Europe PMC (`europepmc`) | Peer-reviewed articles, PMIDs, PMCIDs, abstracts (`claim_source_fit: research_evidence`). |
| **Tier 3** | `SCHOLARLY_METADATA` | Crossref (`crossref`), Semantic Scholar, OpenAlex | DOI metadata resolution, citation graph, author disambiguation (`claim_source_fit: metadata_verification`). |

---

## 3. Evidence Processing Pipeline

All external API responses pass through strict security and integrity controls before entering vector/graph evidence indices:

```text
External API Response (Raw JSON / XML)
                  ↓
       1. HTTPS & Transport Security
                  ↓
       2. Canonical Serialization & SHA-256 Response Hashing
                  ↓
       3. Schema & Type Validation
                  ↓
       4. HTML/XML Stripping & Indirect Prompt-Injection Sanitization
                  ↓
       5. Provenance & Telemetry Metadata Assembly
                  ↓
       6. Document & Entity Normalization
                  ↓
       7. Multi-Source Deduplication (PMID → PMCID → DOI → RxCUI)
                  ↓
       8. Ingestion into Evidence Store & Hybrid Retriever
```

---

## 4. Staged Query Routing

The `EvidenceQueryRouter` routes clinical queries based on risk tier and expected claim type:

```text
Query + Risk Tier (R0–R3)
          ↓
  Query Router Evaluation
    ├─ R0/R1 Factual: PubMed + Europe PMC
    ├─ R2 Interaction/ADEs: PubMed + Europe PMC + openFDA
    ├─ R3 High Risk/Warnings: openFDA + PubMed + RxNorm
    └─ Trial Queries: ClinicalTrials.gov + PubMed
```

---

## 5. Dual Execution Modes

1. **Live API Mode (`LIVE_API_MODE`):** Queries live external REST endpoints with active rate limiting, exponential backoff retries, and short explicit HTTP timeouts.
2. **Frozen Snapshot Mode (`FROZEN_SNAPSHOT_MODE`):** Replays pre-recorded, SHA-256 verified raw JSON response snapshots stored in `experiments/manifests/external_sources_v1.json` to guarantee 100% scientific reproducibility for benchmark evaluation runs.
