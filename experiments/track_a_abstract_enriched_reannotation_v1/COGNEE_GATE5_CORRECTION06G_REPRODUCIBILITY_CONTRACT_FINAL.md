# REPRODUCIBILITY CONTRACT FINAL AUDIT

| Field | Mandatory? | Observable? | Captured? | Compared? | Used for Full Match? |
|-------|------------|-------------|-----------|-----------|----------------------|
| eligibility | YES | YES | YES | YES | YES |
| lock_reason | YES | YES | YES | YES | YES |
| detailed_trust_map | YES | YES | YES | YES | YES |
| grounding_states | YES | YES | YES | YES | YES |
| integrity_states | YES | YES | YES | YES | YES |
| poisoning_states | YES | YES | YES | YES | YES |
| candidate_injection_states | YES | YES | YES | YES | YES |
| query_injection_scan | YES | YES | YES | YES | YES |
| generation_called | YES | YES | YES | YES | YES |
| bstention_called | YES | YES | YES | YES | YES |
| 
umber_of_returned_results | YES | YES | YES | YES | YES |
| 
eturned_document_ids | YES | YES | YES | YES | YES |
| 
eturned_chunk_ids | YES | YES | YES | YES | YES |
| 
eturned_text_hashes | YES | YES | YES | YES | YES |
| 
etrieval_scores | YES | YES | YES | YES | YES |
| dataset_id | YES | YES | YES | YES | YES |
| search_type | YES | YES | YES | YES | YES |
| execution_path_type | YES | YES | YES | YES | YES |
| provenance_status | YES | YES | YES | YES | YES |
| provenance_source | YES | YES | YES | YES | YES |
| provenance_document_id | YES | YES | YES | YES | YES |
| provenance_chunk_id | YES | YES | YES | YES | YES |
| mapping_status | YES | YES | YES | YES | YES |
| ctual_cognee_result_id | YES | NO (UNAVAILABLE) | NO | NO | **NO** |

**Note on Retrieval Identity:**
ctual_cognee_result_id is a mandatory identity field in the conceptual contract. However, the Cognee adapter does not expose a stable underlying UUID independently from the parsed chunk ID. Therefore, it is strictly recorded as UNAVAILABLE.
Because a mandatory field is unavailable, the final strict mathematical conclusion is FULL_CONTRACT_EXACT_MATCH = NOT_ESTABLISHED. The experiment instead proves DECISION_EXACT_MATCH and OBSERVED_RETRIEVAL_EXACT_MATCH.

**Note on Retrieval Score Semantics:**
score_origin: ADAPTER_DERIVED. The 
etrieval_scores field reflects Reciprocal Rank Fusion (
rf_score) assigned post-retrieval by the hybrid adapter, not a native Cognee vector score.
