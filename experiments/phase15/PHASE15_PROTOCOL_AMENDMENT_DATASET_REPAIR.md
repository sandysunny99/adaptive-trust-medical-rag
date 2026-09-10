# Phase 15 Protocol Amendment — Dataset Repair

**Amendment ID:** PA-001
**Date:** 2026-09-08
**Type:** Pre-Execution Data-Quality Correction

## 1. Summary

The originally frozen Phase 15 dataset (`phase15_cases.jsonl`) was structurally invalid. It contained 200 rows but only 6 unique query strings — all were placeholder templates (e.g., `"Test query for PROMPT_INJECTION"`) that could not exercise any security mechanism or pharmacological reasoning in either the baseline or hardened experimental condition.

## 2. Key Facts

- **No experimental observations existed** at the time of discovery. The fail-closed execution check identified the problem before any baseline or hardened runs occurred.
- **No experimental results are being discarded.** The dataset was invalidated before it was used.
- **The dataset replacement was performed entirely before execution**, preserving the pre-registered experimental design.
- **Zero model API calls were made** during dataset reconstruction or validation.

## 3. Protocol Components: Change Status

| Component | Changed? | Notes |
|-----------|----------|-------|
| Paired baseline vs hardened design | NO | |
| N = 200 target | NO | |
| Family counts (35/35/35/35/30/30) | NO | |
| Primary endpoint (SFR) | NO | |
| Primary outcome taxonomy | NO | |
| F1–F12 secondary failure taxonomy | NO | |
| McNemar exact two-sided test | NO | |
| Reproducibility requirements | NO | |
| Baseline/hardened boundary | NO | |
| Model configuration (gemini-3.1-pro-preview) | NO | |
| Phase 14 security architecture | NO | |
| Orchestrator-level scope | NO | |
| Dataset query content | **YES** | Placeholder strings replaced with genuine pharmacological queries and adversarial payloads |
| Dataset SHA-256 | **YES** | New hash reflects new content |
| Dataset freeze metadata | **YES** | Updated in PHASE15_DATASET_FREEZE.json |

## 4. Old vs. New Dataset

| Attribute | Old (Invalid) | New (Corrected) |
|-----------|---------------|-----------------|
| Total cases | 200 | 200 |
| Unique queries | 6 | 200 |
| Drug entities | 0 | 65+ |
| Attack subtypes | 0 | 171 |
| Adversarial payloads | 0 | 35 distinct |
| Evidence fixtures | 0 | 35 distinct |
| Old SHA-256 | `1450057981a7...` | N/A |
| New SHA-256 | N/A | `af71c70d3608...` |

## 5. Scientific Rationale

The original dataset was generated as a structural placeholder during the freeze preparation phase to demonstrate the dataset machinery (case IDs, family balance, SHA-256 hashing). It was never intended as the final experimental stimulus set. The freeze audit verified byte-level integrity and family balance but did not verify query content validity — a gap that has now been addressed.

The corrected dataset was designed with explicit attention to:
- Drug entity diversity (65+ distinct pharmacological entities across multiple drug classes)
- Attack diversity (171 distinct attack subtypes across 6 families)
- Task category diversity (DDI, ADR, MOA, PK, PD, contraindication, toxicology, medication safety)
- Medical accuracy of underlying pharmacological tasks
- Provenance transparency (all cases labeled SYNTHETIC_ADVERSARIAL_FIXTURE or SYNTHETIC_BENCHMARK_QUERY)

## 6. Reproducibility Note

This amendment is part of the experiment's reproducibility record. The fact that the experiment was stopped before invalid stimuli produced results is itself a validation of the fail-closed execution protocol. Future replications should use the corrected dataset hash (`af71c70d3608...`).

The original invalid dataset was never the subject of any scientific observation.

## 7. Adjudication and Final Dataset
Per human research decision, the rebuilt dataset underwent formal case-level proxy adjudication across 5 dimensions (Pharmacological Validity, Security Validity, Stimulus Distinctness, Provenance, Expected Outcome). All 200 cases were verified and accepted. No cases required revision or replacement.

**Chronology:**
1. Placeholder dataset
2. Execution prevented (fail-closed)
3. Synthetic benchmark reconstruction
4. Automated validation
5. Human adjudication (research proxy)
6. Final dataset freeze

## 8. Final Research-Proxy Adjudication
All 200 benchmark cases underwent case-level research-proxy adjudication against five predefined validity dimensions.
No experimental observations were generated from the original placeholder dataset.
