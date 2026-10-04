# CLAIM-LEVEL VS CHUNK-LEVEL DISTINCTION

- **Retrieval**: Chunk level.
- **Trust Scoring**: Chunk level.
- **Relationship Grounding**: Chunk level (pre-generation).
- **NLI Entailment**: Claim level (post-generation).

The system correctly applies semantic entailment at the atomic claim level. However, because structural checks (Trust, Relationship Grounding) are performed *only* at the chunk level pre-generation, the generated claims are immune to relationship constraints if they hallucinate relationships using the text of an otherwise-approved chunk.
