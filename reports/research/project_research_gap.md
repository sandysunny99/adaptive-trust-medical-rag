# Project Research Gap & Open Questions

## Addressed Research Gaps
- Mitigated prompt injection susceptibility in RAG pipelines.
- Resolved unweighted retrieval of outdated or low-authority medical documents.
- Eliminated hallucinated PMIDs/citations in generated responses.

## Open Research Questions & Future Work
1. **Small Language Model (SLM) Security Screening:** Evaluating light SLMs (e.g., 1B-3B parameters) for pre-retrieval injection filtering to reduce latency.
2. **Real-time Knowledge Graph Expansion:** Expanding Neo4j graph candidates dynamically from RxNorm and PubMed APIs.
3. **Multi-lingual Pharmacological Normalization:** Extending entity normalization to multi-lingual drug brand names and international regulatory databases.
