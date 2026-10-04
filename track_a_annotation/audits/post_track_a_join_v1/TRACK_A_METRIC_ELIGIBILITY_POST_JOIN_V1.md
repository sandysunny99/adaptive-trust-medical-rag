# TRACK A METRIC ELIGIBILITY POST JOIN V1

| Metric | Rank Data Available? | Protocol Defined? | K Defined? | Relevance Defined? | Denominator Defined? | Aggregation Defined? | Edge-case rules defined? | Officially Computable? | Reason if blocked |
|---|---|---|---|---|---|---|---|---|---|
| Recall@10 | Yes | Yes | Yes (K=10) | Yes (Binary) | Yes (GT corpus) | Yes | Yes | **OFFICIAL** | None |
| Precision@10 | Yes | Yes | Yes (K=10) | Yes (Binary) | Yes | Yes | Yes | **OFFICIAL** | None |
| MRR | Yes | Yes | Yes | Yes (Binary, first hit) | N/A | Yes | Yes | **OFFICIAL** | None |
| nDCG@10 | Yes | Yes | Yes (K=10) | Yes (Graded) | N/A | Yes | Yes | **OFFICIAL** | None |
| Hit@K | Yes | No | N/A | No | N/A | No | No | **BLOCKED** | Missing specification |
| MAP | Yes | No | N/A | No | N/A | No | No | **BLOCKED** | Missing specification |
