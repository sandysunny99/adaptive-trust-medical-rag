# CLAIM REPRESENTATION AUDIT

- **Authoritative Representation**: `AtomicClaim` in `claim_verifier_v2.py`.
- **Fields**: `text`, `parent_sentence`, `claim_index`, `citation_ids`, `is_critical`, `drug_entities`.
- **Can a claim exist without evidence?**: Yes. The `decompose_into_claims` function parses claims purely from the LLM's text output using regex for sentence/clause boundaries and citations. It does not structurally enforce that a claim *must* be derived from an evidence object.
- **Can it exist without provenance?**: Yes. The LLM can generate a claim without `[Source N]` tags, resulting in empty `citation_ids`.
- **Source/Relationship**: Not structurally represented on the claim itself (only `drug_entities` exists, but not populated during decomposition).
