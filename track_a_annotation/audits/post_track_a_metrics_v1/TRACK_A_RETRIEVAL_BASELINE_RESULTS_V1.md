# TRACK A RETRIEVAL BASELINE RESULTS V1

## Population
- Track A Dataset: 530
- F0 evaluated: 9 queries
- F3 evaluated: 9 queries
- Exclusions: 0 (All queries have GT denominators > 0)

## Results

### F0 (Baseline)
- **Recall@10**: 0.0381
- **Precision@10**: 0.0778
- **MRR**: 0.2346
- **nDCG@10**: 0.4441

### F3 (Reranked)
- **Recall@10**: 0.0286
- **Precision@10**: 0.0889
- **MRR**: 0.1430
- **nDCG@10**: 0.5053

## Metric Definitions
- K=10
- Relevance Definition: Binary for R/P/MRR. Graded (2,1,0) for nDCG.
- Aggregation: Macro-average
- Exclusions: Queries with 0 total relevant chunks (0 found).
