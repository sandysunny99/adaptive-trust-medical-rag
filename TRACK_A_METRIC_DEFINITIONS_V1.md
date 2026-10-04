# TRACK_A_METRIC_DEFINITIONS_V1

## Overview
This document defines the exact formulae and treatments for the retrieval relevance metrics used in Track A.

## 1. Recall@K
- **Definition**: The fraction of all known relevant chunks for a query that are successfully retrieved in the top K positions.
- **Formula**: `(Number of RELEVANT chunks in top K) / (Total number of RELEVANT chunks for the query in the corpus)`
- **Annotation Requirements**: Requires binary relevance (`RELEVANT` = 1, `PARTIALLY_RELEVANT/IRRELEVANT/INSUFFICIENT` = 0).
- **Treatment of No-Relevant-Document Queries**: If a query has 0 known relevant chunks in the entire corpus, it is excluded from the macro-average Recall calculation.

## 2. Precision@K
- **Definition**: The fraction of retrieved chunks in the top K positions that are relevant.
- **Formula**: `(Number of RELEVANT chunks in top K) / K`
- **Annotation Requirements**: Requires binary relevance (`RELEVANT` = 1, `PARTIALLY_RELEVANT/IRRELEVANT/INSUFFICIENT` = 0).

## 3. Normalized Discounted Cumulative Gain (nDCG@K)
- **Definition**: Measures ranking quality by penalizing relevant documents that appear lower in the retrieved list.
- **Formula**: `DCG@K / IDCG@K`
  - `DCG@K = sum_{i=1}^K (2^{rel_i} - 1) / log2(i + 1)`
  - `IDCG@K` is the DCG of the ideal ranking (sorted by `rel_i` descending).
- **Annotation Requirements**: Requires graded relevance mapping.
  - `RELEVANT`: `rel_i = 2`
  - `PARTIALLY_RELEVANT`: `rel_i = 1`
  - `IRRELEVANT` / `INSUFFICIENT_INFORMATION`: `rel_i = 0`
- **Treatment of Missing Evidence**: Evaluated as `rel_i = 0`.
- **Treatment of Ambiguous**: Must be adjudicated to a concrete grade before calculation.

## 4. Mean Reciprocal Rank (MRR)
- **Definition**: The average of the reciprocal ranks of the first relevant chunk retrieved for a set of queries.
- **Formula**: `(1 / |Q|) * sum_{q in Q} (1 / rank_q)` where `rank_q` is the position of the first `RELEVANT` chunk.
- **Annotation Requirements**: Requires binary relevance. `PARTIALLY_RELEVANT` does not count as the first relevant hit for MRR calculation to ensure strict top-result quality.

## Global Conditions
- Chunks marked `AMBIGUOUS` cannot be included in final metric calculations. They must be adjudicated.
- If an abstract is missing and deemed `INSUFFICIENT_INFORMATION`, it acts as an irrelevant result (score 0).
