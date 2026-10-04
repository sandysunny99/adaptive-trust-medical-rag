# TRACK_A_RANK_FIELD_AUDIT_V1

## 1. Audit Objective
To determine if explicit retrieval rank information is natively stored within the 530 records of `TRACK_A_HUMAN_ANNOTATION_DATASET_V1.jsonl`, and to establish how to map it to the annotation workspace without fabricating data.

## 2. Field Analysis
A comprehensive key extraction across all 530 records yields exactly 16 fields:
`['source_url_provenance', 'evidence_span', 'abstract_evidence_context', 'annotator_id', 'relevance_grade', 'annotation_timestamp', 'enrichment_status', 'query', 'source_id', 'rationale', 'schema_version', 'label', 'title', 'chunk_id', 'position_id', 'unique_query_id']`

No fields containing `rank`, `order`, `position_rank`, or similar nested metadata exist in the JSON structure.

## 3. Dataset Limitation Documented
**Rank genuinely does not exist as an explicit field in this JSONL dataset.**
The dataset represents a deduplicated pool of candidate positions retrieved across multiple configuration paths for relevance grading, decoupling the grading task from the retrieval source algorithms. 

## 4. Preservation Strategy
- **Source Field**: None.
- **Mapped Workspace Field**: Removed/Nullified.
- **Number Populated**: 0.
- **Number Missing**: 530.
- **Conclusion**: The absence of `rank` in the workspace is structurally accurate to the source data. We explicitly record this as a DATASET LIMITATION. Rank calculations required for MRR/nDCG will be merged back post-annotation by joining the `position_id` against the raw retrieval logs from `Baseline` and `Cognee`.
