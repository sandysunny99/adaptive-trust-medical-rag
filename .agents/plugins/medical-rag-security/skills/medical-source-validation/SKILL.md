---
name: medical-source-validation
description: Authority tiering, freshness decay calculation, and reputation scoring for evidence sources in medical RAG.
---

# Medical Source Validation Skill

This skill governs how evidence sources are classified, rated, and evaluated for authority and freshness.

## Source Authority Tiers (0 to 5)

| Tier | Authority Score | Source Category | Examples |
|------|-----------------|-----------------|----------|
| **5** | 1.00 | Regulatory Package Inserts / Primary Agency Labels | FDA DailyMed SPL, EMA Summary of Product Characteristics (SmPC) |
| **4** | 0.85 | Major Clinical Practice Guidelines / Systematic Reviews | Cochrane Reviews, USPSTF, NICE Guidelines, Major Professional Societies (AHA, ACC) |
| **3** | 0.70 | Peer-Reviewed Clinical Trials / High-Impact Medical Journals | NEJM, Lancet, JAMA, BMJ, Annals of Internal Medicine |
| **2** | 0.50 | Standard Medical Literature / Observational Studies | Secondary specialty journals, observational cohort studies, case series |
| **1** | 0.30 | Preprints / Preliminary Data | bioRxiv, medRxiv (subject to strict quarantine in high risk queries) |
| **0** | 0.00 | Unverified Web Pages / Forums / Non-authoritative Blogs | Disallowed for clinical pharmacology inference |

## Evidence Freshness Calculation

Freshness decay reflects the medical obsolescence risk:

- **Half-life:** 5 years (1825 days) for general clinical literature; 3 years for fast-evolving pharmacology.
- **Formula:**
  $$\text{FreshnessScore}(t) = \exp\left(-\lambda \cdot \max(0, t_{\text{curr}} - t_{\text{pub}})\right)$$
- **Black-Box Update Override:** If a document is an FDA safety communication or updated black-box warning issued within the last 180 days, assign freshness score = `1.0`.
- **Superseded Flag:** If a newer label or retraction is indexed, mark old records as `superseded` (trust score = `0.0`).
