# EVIDENCE REPRESENTATION AUDIT

- **Authoritative Representation**: `EvidenceChunk` (in verifier context) and `ScoredCandidate` (in orchestrator context).
- **Fields (`EvidenceChunk`)**: `chunk_id`, `text`, `source_authority`, `citation_index`.
- **Missing Fields**: `EvidenceChunk` drops `trust_score`, `freshness`, `poisoning_score`, and `missing_factors`.
- **Distinction**: 
  - *Evidence Text Exists*: Passed to NLI model.
  - *Evidence is Traceable*: Uses `citation_index`.
  - *Evidence is Trusted*: Evaluated pre-generation in `EvidenceEligibilityGate`, but state is NOT passed to the post-generation verifier.
