# REPRODUCIBILITY CONTRACT AUDIT

| Required Field | Protocol Requires? | 06F Captures? | 06F Compares? | Status |
|----------------|--------------------|---------------|---------------|--------|
| eligibility | YES | YES | YES | COMPLIANT |
| lock_reason | YES | YES | YES | COMPLIANT |
| detailed_trust_map | YES | YES | YES | COMPLIANT |
| grounding_states | YES | YES | YES | COMPLIANT |
| integrity_states | YES | YES | YES | COMPLIANT |
| poisoning_states | YES | YES | YES | COMPLIANT |
| candidate_injection_states | YES | YES | YES | COMPLIANT |
| query_injection_scan | YES | YES | YES | COMPLIANT |
| generation_called | YES | YES | YES | COMPLIANT |
| bstention_called | YES | YES | YES | COMPLIANT |
| 
umber_of_returned_results | YES | YES | YES | COMPLIANT |
| 
eturned_document_ids | YES | YES | YES | COMPLIANT |
| 
eturned_chunk_ids | YES | YES | YES | COMPLIANT |
| 
eturned_text_hashes | YES | YES | YES | COMPLIANT |
| 
etrieval_scores | YES | YES | YES | COMPLIANT |
| dataset_id | YES | YES | YES | COMPLIANT |
| search_type | YES | YES | YES | COMPLIANT |
| execution_path_type | YES | YES | YES | COMPLIANT |
| provenance_status | YES | YES | YES | COMPLIANT |
| provenance_source | YES | YES | YES | COMPLIANT |
| provenance_document_id | YES | YES | YES | COMPLIANT |
| provenance_chunk_id | YES | YES | YES | COMPLIANT |
| ctual_cognee_result_id | YES | YES | YES | COMPLIANT (Status recorded as UNAVAILABLE where unsupported by Cognee) |

**Note on retrieval identifier identity:** 
ctual_cognee_result_id is tracked but correctly documented as UNAVAILABLE because the Cognee adapter does not expose a stable retrieval UUID independently from the parsed chunk ID. The chunk ID is correctly tracked as 
eturned_chunk_ids but NOT falsely conflated as a retrieval ID.

**Note on retrieval scores:**

etrieval_scores reflect 
rf_score (Reciprocal Rank Fusion) assigned by the hybrid adapter. These are adapter-derived and explicitly labeled as such in evidence logic.
