# Current Architecture Snapshot
**Commit:** 8741f595f6db0a87b84f50d131b1ff566ee2d6f0
**Python:** 3.12.10

## Router Configuration
- **Retry Policy:** Exponential backoff, jitter, max 3 attempts
- **Circuit Breaker:** 2 consecutive failures -> OPEN for 60s

## Retrieval Configuration
- **Channels:** BM25, Dense (SimpleEmbeddingModel), Graph
- **Fusion:** Reciprocal Rank Fusion (k=60, top_n=50)
- **Top-K:** 10
- **Corpus:** manifest.json (4 documents)

## Security Modules
- **Input:** sanitize_query (markdown stripping, injection markers)
- **Injection:** Regex/heuristics block on exact matches
- **Poisoning:** SHA-256 validation against corpus manifest
- **Trust:** AdaptiveTrustScorer (authority, entity, freshness, reputation)
- **Eligibility:** Risk-tier thresholds (R0:0.3, R1:0.45, R2:0.60, R3:0.75)
- **Safety:** Post-generation verification
- **Verification:** NLI-based check against chunks
- **Abstention:** Required when gates fail or evidence is insufficient

## Generation
- **Provider:** RoutedLLMBackend (Gemini primary, Groq secondary)
