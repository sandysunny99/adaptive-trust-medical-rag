# Phase 2C: Biomedical Embedding Evaluation (v2)

## 1. Objective
To evaluate alternative dense embedding candidates against the Phase 2B.2 (v2.1) diagnostic benchmark and verify the mechanism of semantic retrieval degradation during Reciprocal Rank Fusion (RRF).

## 2. Benchmark Version
- **Version**: V2.1 Diagnostic Benchmark (Frozen)
- **Scale**: 77 documents, 19 cases, 6 positive cases
- **Limitation**: This remains a diagnostic benchmark due to the limited positive case count. Results demonstrate algorithmic differences but are not final model-selection evidence.

## 3. Candidates Evaluated
- **E0 (Baseline)**: `SimpleEmbeddingModel` (7-dimensional toy vocabulary)
- **E1 (S-PubMedBERT)**: `pritamdeka/S-PubMedBert-MS-MARCO` (Passage-retrieval focus)
- **E2 (SapBERT)**: `cambridgeltl/SapBERT-from-PubMedBERT-fulltext` (Biomedical entity focus)

## 4. Dense-Only Results (R1)
*Evaluated on the 6 positive-evidence E-Set cases.*

| Candidate | Recall@5 | MRR |
| :--- | :--- | :--- |
| **E0** (Toy) | 0.000 | 0.000 |
| **E1** (S-PubMedBERT) | **1.000** | 0.867 |
| **E2** (SapBERT) | **1.000** | 0.875 |

*Finding: Both E1 and E2 perfectly restored semantic retrieval capability on the diagnostic subset. E0 failed entirely.*

## 5. Full Hybrid Results (R3)
*R3 = BM25 + Dense + Graph (RRF fusion).*

| Candidate | Recall@5 | MRR |
| :--- | :--- | :--- |
| **E0** (Toy) | 0.667 | 0.500 |
| **E1** (S-PubMedBERT) | 0.667 | 0.667 |
| **E2** (SapBERT) | 0.667 | 0.688 |

*Finding: Hybrid retrieval with legitimate embeddings performed WORSE than Dense-only.*

## 6. Fusion Diagnostic (R3 Degradation)
To determine whether RRF was the true bottleneck, we extracted the actual channel rankings for an inverted case (**Case e-12**: "Is electrocardiogram monitoring required for citalopram?").

**Actual Channel Trace for Expected Document (42326111):**
* Dense Rank (SapBERT): 4
* BM25 Rank: `inf` (Failed to match keywords)
* Graph Rank: `inf`
* **RRF Score**: 0.0156 (1 / 64)

**Actual Channel Trace for Noise Document (42062777):**
* Dense Rank: 10
* BM25 Rank: 2
* Graph Rank: `inf`
* **RRF Score**: 0.0304 (1/70 + 1/62)

**FUSION BOTTLENECK CONFIRMED**: 
The degradation is directly caused by naïve RRF (k=60) treating BM25 noise as additive. Because BM25 completely misses paraphrased documents, the true semantic document receives a score from only one channel. A noise document that matches superficial keywords (e.g., "monitoring") receives scores from BOTH BM25 and Dense, mathematically overpowering the single-channel semantic match and pushing the true document completely out of the Top-5.

## 7. Next Steps & Decision
**Decision: FUSION_BOTTLENECK_REQUIRES_SEPARATE_EXPERIMENT**

The empirical diagnostic establishes that replacing E0 with E1/E2 solves semantic retrieval perfectly, but the existing RRF fusion degrades it. 

We must pause embedding selection and proceed to **Phase 2D: Fusion Evaluation** to test:
1. Dynamic channel weighting (discounting BM25 for paraphrase queries)
2. Weighted RRF
3. Cross-Encoder reranking