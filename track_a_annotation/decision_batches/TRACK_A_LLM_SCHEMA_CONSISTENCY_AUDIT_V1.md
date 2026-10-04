# TRACK_A_LLM_SCHEMA_CONSISTENCY_AUDIT_V1
The adapter code strictly enforces label-to-grade mappings post-schema validation.
Any mismatch between proposed_label and proposed_grade triggers a SEMANTIC_SCHEMA_CONSISTENCY_FAILED.
