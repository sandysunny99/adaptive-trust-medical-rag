# TRACK A RETRIEVAL METRIC ELIGIBILITY V1

| Metric | Defined in protocol? | Required inputs | Inputs available? | Relevance mapping | K | Denominator | Aggregation | Edge-case rule | Status | Blocking issue |
|---|---|---|---|---|---|---|---|---|---|---|
| Recall@K | Yes | rank, label, query denominator | No (missing rank, denominator) | Binary | Missing | Total query relevant | Macro-average | Exclude 0-relevant | BLOCKED BY MISSING DATA | Missing `rank` & denominator |
| Precision@K | Yes | rank, label | No (missing rank) | Binary | Missing | K | Macro-average | - | BLOCKED BY MISSING DATA | Missing `rank` |
| Hit@K | No | rank, label | No | Missing | Missing | N/A | Missing | - | BLOCKED BY MISSING SPECIFICATION | Missing protocol definition |
| MRR | Yes | rank, label | No (missing rank) | Binary (First RELEVANT only) | N/A | | Macro-average | - | BLOCKED BY MISSING DATA | Missing `rank` |
| nDCG@K | Yes | rank, label | No (missing rank) | Graded (0,1,2) | Missing | IDCG | Macro-average | Missing evidence = 0 | BLOCKED BY MISSING DATA | Missing `rank` |
| MAP | No | rank, label | No | Missing | N/A | Missing | Missing | - | BLOCKED BY MISSING SPECIFICATION | Missing protocol definition |
