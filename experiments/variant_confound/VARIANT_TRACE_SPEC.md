# Variant Trace Specification (GATE 7)

## Trace Output Format
Each case executed during development evaluation MUST emit a structured JSON trace conforming to the `LiveVariantResult` dataclass schema from `live_variants.py`.

## Required Trace Fields

- **query_id**: Uniquely identifies the case (`case.case_id`).
- **variant_id**: Evaluated variant (`A`, `B`, `C`, `D`, `E`, or `F`).
- **query_hash**: SHA-256 hash of the `query` text for deterministic provenance.
- **normalized_query**: The output of `sanitize_query` (in F) or unaltered (B-E).
- **query_drugs**: Array of resolved RxNorm / generic entities from the normalizer.
- **retrieval_config_hash**: Deterministic hash of the active retrieval topology and parameters.
- **retrieval_candidate_ids**: Ordered array of chunk IDs directly returned by the retriever *prior* to trust gating.
- **retrieval_candidate_order**: Final RRF ranks of the candidates.
- **retrieval_scores**: Array of mapping scores (e.g., RRF score).
- **context_hash**: SHA-256 hash of the final `prompt` text injected into the LLM adapter.
- **generation_config_hash**: Hash of the target LLM configuration.
- **security_config_hash**: Hash representing active pre/post gates and trust threshold logic.
- **provider**: Dynamic string from the `LLMProviderRouter` (e.g., `gemini`, `groq`).
- **model**: specific model ID (e.g., `gemini-2.5-pro`).

## Data Privacy Constraint
No patient identities or real PHI may be traced.
No API keys or system tokens may be traced.
All queries must correspond strictly to synthetic dataset hashes.
