# Free Replication Compatibility Analysis

## The Issue
The `FREE_REPLICATION_V1` experiment is designed to test the RAG architecture using a lower-tier/free provider (Groq/Llama or OpenAI OSS models). The protocol for this experiment (`FREE_REPLICATION_V1_PROTOCOL.md`) explicitly specifies the LLM provider and model but is **silent on the embedding model**.

Because the project currently uses `SimpleEmbeddingModel` in its default orchestrator retrieval path, any recent test of `FREE_REPLICATION_V1` would have inadvertently executed using the 7-dim test fixture.

## Impact of Adopting S-PubMedBert

If `pritamdeka/S-PubMedBert-MS-MARCO` is explicitly authorized as the Gate 5 baseline:

1.  **Comparability Break**: Any existing `FREE_REPLICATION_V1` results that relied on `SimpleEmbeddingModel` will become mathematically incomparable to the new baseline.
2.  **Protocol Amendment**: The `FREE_REPLICATION_V1_PROTOCOL.md` (or a global experiment master protocol) must be amended to explicitly mandate the same semantic embedding model to ensure the only independent variable is the LLM generator.
3.  **Model Version Freeze**: The exact HuggingFace revision hash for `S-PubMedBert-MS-MARCO` must be frozen in the configuration to guarantee deterministic retrieval across both standard Gate 5 and Free Replication runs.

## Conclusion
Adopting `S-PubMedBert` is the correct scientific path because `SimpleEmbeddingModel` produces zero-vectors for key test queries, rendering the dense retrieval evaluation meaningless. However, making this change requires an explicit amendment to the experiment protocols and invalidation of prior `FREE_REPLICATION_V1` results that relied on the test fixture.

`evidence_source`: `manual_analysis`
