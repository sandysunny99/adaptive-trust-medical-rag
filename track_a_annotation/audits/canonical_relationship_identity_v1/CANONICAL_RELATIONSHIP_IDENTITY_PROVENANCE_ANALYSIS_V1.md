# Canonical Relationship Identity Provenance Analysis

## Current Provenance State
The system heavily enforces document and chunk provenance:
- Each `Candidate` and `EvidenceChunk` carries `source_authority`, `document_id`, `chunk_id`, and `citation_index`.
- Claims are traced back to `citation_index`.

## The Identity Provenance Gap
While the **textual chunk** has provenance, the **semantic identity** does not.
If a generated claim asserts: `Aspirin -> INHIBITS -> Warfarin`:
1. Where did the `Aspirin` identity (`RxCUI 1191`) come from? (The prompt? The text chunk?)
2. Where did the `Warfarin` identity (`RxCUI 11289`) come from?
3. Which exact chunk established the `INHIBITS` predicate?

Currently, because Canonical Relationship Identity is not preserved, there is no way to connect the mathematical/semantic identity of the claim to the specific chunk's provenance. The system simply says "This text string was derived from this document." 

## Interaction with P0 Provenance Enforcement
The Trust P0 Remediation strictly enforced that claims must tie back to citations. However, if the citation supports the general topic but the LLM hallucinated a direction swap (A inhibits B instead of B inhibits A), the P0 provenance check passes because the citation exists and textually entails the context. Adding Canonical Identity Provenance would require that the source explicitly output a matching `CanonicalRelationshipIdentity` structure bound to the exact same citation.

## Recommendation
A future `CanonicalRelationshipIdentity` object must include a `provenance` field indicating the `chunk_id` and `source_authority` that explicitly established the relationship, extending the P0 enforcement to the semantic level, not just the text level.
