# Phase 2A: Retrieval Forensics (TOY-CORPUS BASELINE)

## 1. Actual Implementations Audit

This document traces the exact algorithmic implementations of the existing `HybridRetrievalEngine` components to establish the true retrieval baseline before any Phase 2 implementation.

### A. Lexical Retrieval (`BM25Retriever`)
- **Algorithm:** Okapi BM25 (Pure-Python implementation).
- **Tuning:** `k1 = 1.5` (term frequency saturation), `b = 0.75` (document length normalization).
- **Tokenization:** Basic internal text tokenization (`_tokenize(c.text)`). No specialized medical tokenization is utilized (e.g., no stemming or lemmatization of pharmacological terms).

### B. Semantic Retrieval (`VectorRetriever`)
- **Algorithm:** Dense vector retrieval using cosine similarity (`_cosine_similarity(query_emb, self._embeddings[i])`).
- **Embedding Model:** Accepts any `EmbeddingModel` protocol. Currently uses a generic in-memory encoder for testing (e.g., in `LiveModelAdapter` or mock setups), without a dedicated biomedical model.
- **Index:** Operates entirely in-memory during tests, though comments indicate a future `pgvector` ANN index.

### C. Knowledge Graph Retrieval (`GraphRetriever`)
- **Algorithm:** In-memory adjacency-list BFS traversal (max 2 hops).
- **Edge Semantics:** Explicit `DrugRelationship` objects (e.g., `contraindicated`, `severe`, `moderate`).
- **Scoring:** Hardcoded mapping based on interaction severity (`contraindicated: 1.0`, `severe: 0.9`, `moderate: 0.6`, `mild: 0.3`). This bypasses traditional semantic relevance entirely in favor of known clinical hazards.

### D. Fusion & Ranking (`reciprocal_rank_fusion`)
- **Algorithm:** RRF formula: `1.0 / (k + rank)`.
- **Tuning:** Constant `k = 60`.
- **Tie Handling:** Relies on Python's stable sort of the summed `rrf_score` descending. No tie-breaking logic.

### E. Evidence Eligibility & Trust (`TrustScorer`)
- **Position:** The Trust Scoring and Evidence Eligibility gates occur *downstream* of retrieval.
- **Mechanics:** Candidates are fetched, fused, and ranked by the engine, *then* filtered/quarantined if `poisoning_score > 0.4`. Actual `TrustScorer` evaluations (authority, freshness) are performed on the top K results *post-retrieval*, meaning highly trusted but poorly embedded documents may never reach the gate.

## 2. Identified DDI/ADE Weaknesses in Baseline

1. **Vocabulary Mismatch (Lexical):** Generic tokenization struggles with drug salts (e.g., "metformin hydrochloride" vs "metformin"), trade names, and abbreviations, causing BM25 misses.
2. **Generic Embeddings (Semantic):** Generic embedding models collapse complex pathway terms (e.g., "CYP3A4 inhibitor" vs "CYP2D6 substrate") into similar vectors, leading to high cosine similarity for unrelated DDIs.
3. **Graph Dependency (Graph):** Relies on a pre-populated static edge list. Missing edges return nothing.
4. **Trust-Agnostic Ranking (Fusion):** RRF treats the three channels equally. An untrusted blog post with high lexical overlap will outrank a heavily trusted FDA label with low lexical overlap.

## 3. Phase 2A Retrieval Evaluation Design

We will build a **Retrieval-Only Evaluation Harness** measuring the following metrics on frozen case data *before* LLM generation:
- `Recall@1`, `Recall@3`, `Recall@5`, `Recall@10`
- `Precision@5`, `MRR`, `nDCG@5`
- **Domain metrics:** Drug entity recall, Interaction evidence recall, ADE evidence recall, Source-authority coverage.

**Controlled Ablation Variants (R0-R4):**
- **R0:** Lexical-only (`BM25Retriever`)
- **R1:** Dense-only (`VectorRetriever` with generic model)
- **R2:** Hybrid (`BM25` + `Dense`)
- **R3:** Full Hybrid (`BM25` + `Dense` + `Graph`)
- **R4:** Full Hybrid + Trust-aware reranking

### Next Immediate Action (Phase 2A.1/2A.2)
Implement the `retrieval-only` evaluation harness against the `live-smoke-v1` cases. Measure R0-R3 baselines on pharmacology, DDI, and ADE subsets to isolate exactly where the current engine loses clinical evidence.
