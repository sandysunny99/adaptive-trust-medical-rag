# Phase 2D.2: Cross-Encoder Reranking Evaluation

## 1. Methodology & Objective
- **Dataset**: V2.1 Diagnostic Benchmark (Frozen)
- **Primary Encoder**: `E1` (`pritamdeka/S-PubMedBert-MS-MARCO`)
- **Fusion Control**: `F0` (Current RRF, k=60, equal weights)
- **Reranker Candidate**: `F3` (`cross-encoder/ms-marco-MiniLM-L-6-v2`)
- **Candidate Pool Size**: N = 20

To verify whether a cross-encoder can recover the semantic documents that were demoted by naïve RRF fusion, we generated a Top-20 candidate pool using `F0` and re-scored it using the `F3` cross-encoder.

## 2. Overall Metrics

| Metric | F0 (RRF) | F3 (Cross-Encoder) |
| :--- | :--- | :--- |
| **Recall@5** | 0.667 | 0.667 |
| **MRR** | 0.667 | 0.667 |

## 3. Rank Recovery Analysis
We analyzed the specific ranking inversions (where the Dense channel successfully retrieved the document, but F0 demoted it out of the Top-5). 

- **Total Inversions (F0 Rank > 5)**: 2 (`e-12`, `e-14`)
- **Recovered by F3 (F3 Rank <= 5)**: 0
- **Regression by F3 (F0 <= 5 AND F3 > 5)**: 0

### Case `e-12` (Citalopram ECG monitoring)
- **F0 Rank**: 11
- **F3 Rank**: 7
- **Result**: `F3` recognized the semantic relevance better than RRF, pulling the document up 4 spots, but **failed to recover** it into the target Top-5.

### Case `e-14` (Doxorubicin cardiotoxicity)
- **F0 Rank**: 14
- **F3 Rank**: 17
- **Result**: `F3` actively degraded the ranking for this case.

## 4. Latency
- **Candidate Pool Generation**: ~120 ms
- **F3 Cross-Encoder Scoring (20 pairs)**: ~850 ms
- **Result**: The addition of a local cross-encoder added nearly 1 second to retrieval latency.

## 5. Limitations & Next Steps (V2.1 Benchmark)
The tested cross-encoder (`ms-marco-MiniLM-L-6-v2`) was selected for retrieval suitability, but its lack of biomedical domain specialization likely explains its failure to fully recover the clinical cases (`e-12`, `e-14`). 

## 6. Decision Gate
**Decision: F3_NOT_BETTER_THAN_F0**

The current cross-encoder candidate did not produce sufficient improvement to justify the massive 700% latency penalty over standard RRF. It improved rank for one inversion (`e-12`) but degraded another (`e-14`), resulting in identical Recall@5 scores to `F0`.

The root problem (Fusion Bottleneck) remains unsolved on this diagnostic benchmark.

**Production Integration**: Do not modify `HybridRetrievalEngine` defaults. The F3 evaluation failed to produce a viable replacement for F0.