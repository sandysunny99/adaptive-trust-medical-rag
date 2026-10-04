# Gate 5 Baseline Model Protocol Amendment V1

## Decision Record
This document serves as a formal amendment to the Gate 5 experimental baseline definition. 

**Formally Designated Gate 5 Dense Baseline Model:**  
`pritamdeka/S-PubMedBert-MS-MARCO`

## Reason for Authorization
1. **Historical Use:** This model was historically used across all major project experiments (`fusion-evaluation-v3`, screening tests, and baseline phase 2 evaluations).
2. **Experiment Manifests:** It is explicitly recorded in `fusion-evaluation-v3-real/manifest.json` and `fusion-evaluation-v3-confirmed/manifest.json` as the `embedding_model`.
3. **Architecture Compatibility:** `docs/ARCHITECTURE.md` explicitly specifies `VECTOR(768)`. S-PubMedBert provides 768-dimensional embeddings, making it structurally compatible with the existing database schema.
4. **Implementation Quality:** It is a real semantic biomedical embedding implementation, capable of generating dense vectors for the required pharmacological terminology.
5. **Continuity:** Adopting it ensures continuity with the project's historical dense retrieval experiments.

## Protocol Context
The original `FREE_REPLICATION_V1` protocol explicitly specified the generation model constraints (`openai/gpt-oss-120b`, Groq provider) but did NOT explicitly specify a dense embedding model. 

Because the protocol was silent on the embedding model, the orchestrator path inadvertently used `SimpleEmbeddingModel`. This amendment explicitly resolves that ambiguity.

## Classification of Prior Implementation
`SimpleEmbeddingModel` is formally classified as a **historical engineering/test fixture only**. It is NOT the Gate 5 semantic baseline and its usage in historical `FREE_REPLICATION` experiments renders those experiments incomparable to the true dense retrieval protocol.

`evidence_source`: `manual_analysis`
