# TRACK A RETRIEVAL METRIC SPECIFICATION AUDIT V1

## Metric Classifications

- **Recall@K**: PROTOCOL-DEFINED (TRACK_A_METRIC_DEFINITIONS_V1.md). Binary relevance mapping. Zero-relevant queries excluded. BLOCKED BY MISSING DATA (rank, K, denominator).
- **Precision@K**: PROTOCOL-DEFINED (TRACK_A_METRIC_DEFINITIONS_V1.md). Binary relevance mapping. BLOCKED BY MISSING DATA (rank, K).
- **nDCG@K**: PROTOCOL-DEFINED (TRACK_A_METRIC_DEFINITIONS_V1.md). Graded mapping (RELEVANT=2, PARTIALLY_RELEVANT=1). AMBIGUOUS must be adjudicated. BLOCKED BY MISSING DATA (rank).
- **MRR**: PROTOCOL-DEFINED (TRACK_A_METRIC_DEFINITIONS_V1.md). Binary (First RELEVANT hit only). BLOCKED BY MISSING DATA (rank).
- **Hit@K**: BLOCKED BY MISSING SPECIFICATION. (Not found in definition artifacts).
- **MAP**: BLOCKED BY MISSING SPECIFICATION. (Not found in definition artifacts).

*All officially defined metrics are currently BLOCKED from calculation on the standalone canonical dataset due to the explicit absence of `rank` and retrieval condition metadata. Per `TRACK_A_RANK_FIELD_AUDIT_V1.md`, rank must be merged from raw retrieval logs.*
