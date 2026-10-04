# TRACK A METRIC PROVENANCE AUDIT

Every aggregate metric result derives from a strict provenance chain:

| Step | Provenance | Source Artifact |
|------|------------|-----------------|
| **1. Track A Position** | 530 evaluated canonical positions | TRACK_A_CANONICAL_STATE_V2.jsonl |
| **2. Query Mapping** | 9 evaluation queries matched by text | TRACK_A_QUERY_POSITION_STRUCTURE_V1.json |
| **3. Rank Resolution** | Retrieved rank extracted via deterministic exact join | 0_results.jsonl & 3_results.jsonl |
| **4. Ground Truth** | Denominators resolved for Recall@10 | 
etrieval_ground_truth_v3_confirmed.json |
| **5. Relevance Mapping** | Graded (0/1/2) and Binary (0/1) mappings applied | TRACK_A_METRIC_DEFINITIONS_V1.md |
| **6. Calculation** | Exact mathematical application of K=10 | post_track_a_metrics.py (Methods A/B) |
| **7. Aggregation** | Macro-averaging over 9 queries | TRACK_A_RETRIEVAL_METRICS_QUERY_LEVEL_V1.jsonl |

**Provenance Verification Status**: VERIFIED
