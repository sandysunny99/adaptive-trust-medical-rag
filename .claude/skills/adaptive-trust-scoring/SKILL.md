---
name: adaptive-trust-scoring
description: Multi-factor trust scoring algorithms, risk-dependent weighting, and threshold gating for medical RAG.
---

# Adaptive Trust Scoring Skill

This skill defines the multi-factor scoring mathematical engine that computes composite trust scores for retrieved evidence chunks.

## Multi-Factor Trust Formula

For a document chunk $d$ under query $q$, risk class $R \in \{\text{R0}, \text{R1}, \text{R2}, \text{R3}\}$, and extracted entities $E$:

$$\text{TrustScore}(d, q, R) = \sum_{i} w_i(R) \cdot S_i(d, q, E)$$

Where $\sum w_i(R) = 1.0$, and the factor scores $S_i \in [0, 1]$ represent:

1. **$S_{\text{auth}}$ (Source Authority):** Tiered authority score (0.0 to 1.0).
2. **$S_{\text{relevance}}$ (Query Relevance):** Cross-encoder / semantic similarity score.
3. **$S_{\text{quality}}$ (Evidence Quality):** Study design quality, sample size, or regulatory label status.
4. **$S_{\text{freshness}}$ (Freshness):** Time-decayed freshness score.
5. **$S_{\text{consistency}}$ (Cross-Source Consistency):** Consensus score across independent sources.
6. **$S_{\text{entity}}$ (Entity Match):** Exact RxCUI / entity alignment score.
7. **$S_{\text{population}}$ (Population Match):** Alignment with specified patient cohort.
8. **$S_{\text{anti\_poison}}$ ($1 - \text{PoisoningScore}$):** Anomaly/adversarial penalty.
9. **$S_{\text{anti\_inject}}$ ($1 - \text{InjectionScore}$):** Indirect injection penalty.

## Weight Configuration (`config/trust.yaml`)

| Factor | R0 (Info) | R1 (Standard) | R2 (Caution) | R3 (Critical) |
|--------|-----------|---------------|--------------|---------------|
| `source_authority` | 0.15 | 0.20 | 0.25 | **0.30** |
| `query_relevance` | **0.20** | **0.20** | 0.15 | 0.10 |
| `evidence_quality` | 0.10 | 0.15 | 0.20 | **0.25** |
| `freshness` | 0.10 | 0.10 | 0.10 | 0.10 |
| `consistency` | 0.15 | 0.10 | 0.10 | 0.10 |
| `entity_match` | 0.10 | 0.10 | 0.10 | 0.10 |
| `population_match` | 0.05 | 0.05 | 0.05 | 0.03 |
| `anti_poisoning` | 0.10 | 0.05 | 0.03 | 0.01 |
| `anti_injection` | 0.05 | 0.05 | 0.02 | 0.01 |

## Eligibility Thresholds

- **R0 Threshold:** $\ge 0.30$
- **R1 Threshold:** $\ge 0.45$
- **R2 Threshold:** $\ge 0.60$
- **R3 Threshold:** $\ge 0.75$

Chunks falling below the risk threshold are disqualified from generation context.
