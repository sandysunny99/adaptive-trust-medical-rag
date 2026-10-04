# TRACK A METRIC NUMERICAL RESULTS AUDIT

## Overview
This audit extracts the exact numerical results for the official Track A retrieval evaluation (F0 Baseline vs F3 Reranked) calculated over the frozen 530-position dataset.

## Extracted Values

### Recall@10
- **F0 Baseline**: 0.0381
- **F3 Reranked**: 0.0286
- **Denominator Definition**: Ground truth expected relevant documents from 
etrieval_ground_truth_v3_confirmed.json.
- **Evaluated Queries**: 9 (all with denominator > 0).
- **Calculation Status**: VERIFIED

### Precision@10
- **F0 Baseline**: 0.0778
- **F3 Reranked**: 0.0889
- **Denominator Definition**: K=10.
- **Evaluated Queries**: 9.
- **Calculation Status**: VERIFIED

### MRR
- **F0 Baseline**: 0.2346
- **F3 Reranked**: 0.1430
- **Denominator Definition**: 1 / rank of first relevant chunk.
- **Evaluated Queries**: 9.
- **Calculation Status**: VERIFIED

### nDCG@10
- **F0 Baseline**: 0.4441
- **F3 Reranked**: 0.5053
- **Denominator Definition**: Ideal DCG ordered by graded relevance (2, 1, 0) up to K=10.
- **Evaluated Queries**: 9.
- **Calculation Status**: VERIFIED

## Consistency Audit
- **K=10 compliance**: PASS
- **GT Denominator compliance**: PASS
- **530/530 Position Coverage**: PASS
- **No missing/duplicate ranks**: PASS
- **Independent Recomputation**: PASS (Method A and B matched perfectly)
