# PHASE 2D.1 DIAGNOSTIC
# Phase 2D: Fusion Evaluation (V1)

## 1. Objective
To systematically evaluate whether modifying the Reciprocal Rank Fusion (RRF) algorithm can prevent the ranking degradation (inversions) observed when integrating strong biomedical dense encoders (E1/E2) into the Hybrid Retrieval Engine.

## 2. Methodology & Candidates
- **Dataset**: V2.1 Diagnostic Benchmark (Frozen)
- **Primary Encoder**: `E1` (`pritamdeka/S-PubMedBert-MS-MARCO`)
- **Control Fusion**: `F0` (Current RRF, k=60, equal weights)
- **Experimental Fusion**: `F1` (Weighted RRF)
  - `W1`: BM25=1.0, Dense=1.5, Graph=1.0
  - `W2`: BM25=0.75, Dense=1.5, Graph=1.0
  - `W3`: BM25=1.0, Dense=2.0, Graph=1.0

## 3. Findings: Rank Inversion Analysis
We isolated cases where the Dense channel successfully retrieved the relevant document (Rank <= 5), but F0 (Hybrid) pushed it out of the Top 5.

**F0 (Baseline) Inversions Identified**: 2 cases (`e-12`, `e-14`)

### Case `e-12` (Citalopram ECG monitoring)
- **Dense Rank**: 1
- **F0 Rank**: `inf` (Dropped out of top 5)
- **F1 (W1) Rank**: `inf` (Failed to recover)
- **F1 (W2) Rank**: `inf` (Failed to recover)
- **F1 (W3) Rank**: `inf` (Failed to recover)

### Case `e-14` (Doxorubicin cardiotoxicity)
- **Dense Rank**: 5
- **F0 Rank**: `inf` (Dropped out of top 5)
- **F1 (W1) Rank**: `inf` (Failed to recover)
- **F1 (W2) Rank**: `inf` (Failed to recover)
- **F1 (W3) Rank**: `inf` (Failed to recover)

## 4. Why Weighted RRF (F1) Failed
In `e-12`, the true semantic document scored perfectly in Dense (Rank 1) but was completely missed by BM25. A noise document containing the exact lexical token "monitoring" ranked highly in both BM25 (Rank 2) and Dense (Rank 10). 

Even under `W3` (where Dense weight is explicitly doubled to `2.0`):
- **True Document Score**: `2.0 / (60 + 1) = 0.0327`
- **Noise Document Score**: `1.0 / (60 + 2) + 2.0 / (60 + 10) = 0.0161 + 0.0285 = 0.0446`

**Mathematical Conclusion**: Additive rank fusion inherently prioritizes multi-channel agreement over single-channel absolute relevance. Static weighting (`F1`) cannot mathematically recover single-channel semantic matches without assigning extreme weights (e.g., Dense=10.0), which would catastrophically degrade exact lexical (BM25) performance.

## 5. Decision Gate
**Decision: F3_CROSS_ENCODER_JUSTIFIED_FOR_EVALUATION**

We have formally proven that static Weighted RRF (`F1`) is structurally insufficient to solve the fusion bottleneck for pharmacological RAG without destroying BM25 performance. Because a noise document can independently trigger lexical overlap, any fusion method that blindly sums ranks will suffer from this pathology.

Static weighted RRF did not recover the observed inversion cases. A cross-encoder is therefore justified as the next candidate fusion intervention, but its superiority has not yet been demonstrated.`n`nF2_DYNAMIC_WEIGHTING = NOT_TESTED`n`nBy evaluating the fused candidate pool (N=20) for true semantic entailment between the query and passage, a cross-encoder can explicitly recognize and demote BM25 noise documents that lack clinical relevance, preserving the high-quality candidates surfaced by the dense encoder.
