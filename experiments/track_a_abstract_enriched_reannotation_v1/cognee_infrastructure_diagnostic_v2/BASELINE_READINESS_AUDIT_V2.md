# BASELINE READINESS AUDIT V2

## 1. BaseAdapterMock Classification

**Classification: TEST FIXTURE ONLY**

`BaseAdapterMock` in [`cognee_gate5_full_rerun.py`](file:///c:/Users/sunny/Downloads/CASE%20STUDY/experiments/cognee_gate5_full_rerun.py) (lines 121-137) has the following implementation:

```python
class BaseAdapterMock:
    def __init__(self, manifest):
        self.manifest = manifest
    def retrieve(self, query: str, **kwargs) -> list[ScoredCandidate]:
        results = []
        for did, chunks in self.manifest.items():
            for cid, meta in chunks.items():
                c = Candidate(...)
                results.append(ScoredCandidate(candidate=c, rrf_score=0.9))
        return results
```

This returns **ALL documents for EVERY query** with a hardcoded `rrf_score=0.9`. It does not perform:
- Query-conditioned retrieval
- BM25 lexical matching
- Dense vector similarity
- Knowledge graph traversal
- RRF fusion

The `TamperingRetrievalWrapper` then filters to `target_doc`, making retrieval entirely case-definition-driven rather than query-driven.

| Property | BaseAdapterMock | Required for Baseline |
|----------|-----------------|----------------------|
| Query-conditioned | ✗ No | ✓ Yes |
| Multi-channel (BM25/Vector/Graph) | ✗ No | ✓ Yes |
| RRF fusion | ✗ No | ✓ Yes |
| Corpus-based | ✗ No (manifest iterator) | ✓ Yes |
| Deterministic by design | ✓ Yes (always all docs) | Depends |
| Target-doc filtering | ✓ (in wrapper) | ✗ Not authorized |

**BASELINE_FULL_GATE5_READINESS = NOT_ESTABLISHED**

## 2. The Authorized Baseline: HybridRetrievalEngine

The actual baseline retrieval engine is [`HybridRetrievalEngine`](file:///c:/Users/sunny/Downloads/CASE%20STUDY/src/adaptive_trust_medical_rag/retrieval/hybrid_retrieval.py#L357-L421) (lines 357-421):

```python
class HybridRetrievalEngine:
    def __init__(self, corpus, embedding_model, *, rrf_k=60, top_n=50, top_k=10):
        self.bm25 = BM25Retriever(corpus)
        self.vector = VectorRetriever(corpus, embedding_model)
        self.graph = GraphRetriever(corpus)

    def retrieve(self, query, query_drugs=None, top_k=None):
        bm25_results = self.bm25.retrieve(query, top_k=self._top_n)
        vector_results = self.vector.retrieve(query, top_k=self._top_n)
        graph_results = self.graph.retrieve(query_drugs or [], top_k=self._top_n)
        fused = reciprocal_rank_fusion([bm25_results, vector_results, graph_results])
        clean = [sc for sc in fused if sc.candidate.poisoning_score <= 0.4]
        return clean[:effective_top_k]
```

This is:
- **Query-conditioned**: BM25 and vector channels match against the actual query text
- **Multi-channel**: Three independent retrieval channels (BM25, dense vector, knowledge graph)
- **RRF-fused**: Reciprocal Rank Fusion with k=60
- **Corpus-based**: Initialized with a `list[Candidate]` evidence corpus
- **Poisoning-filtered**: Candidates with `poisoning_score > 0.4` are removed

## 3. Required Changes for Full Gate 5

The next Full Gate 5 must use `HybridRetrievalEngine` as the Baseline retrieval adapter:

1. Build a `list[Candidate]` corpus from the fixture documents
2. Use a real or test `EmbeddingModel` (e.g., `SimpleEmbeddingModel` from `live_variants.py`)
3. Initialize `HybridRetrievalEngine(corpus, embedding_model)`
4. Call `engine.retrieve(query)` for each Baseline case
5. Do NOT filter results by target document — let the query-conditioned retrieval and the downstream security pipeline determine what passes

This ensures the Baseline path is experimentally comparable to the Cognee path.
