# GATE 5 RETRIEVAL QUALIFICATION REPORT
**Status**: `RETRIEVAL_QUERY_ALIGNMENT_ISSUE` + `RETRIEVAL_ENGINE_BUG`

## 1. Executive Summary
The isolated diagnostic pipeline was executed to rigorously isolate the 0-candidate retrieval failures observed in the Full Gate 5 Harness Readiness test. The hypothesis that "Cognee infrastructure is broken" and "prune_system() is the root cause" is fully **falsified**. 

Live retrieval via both direct `cognee.search()` and the `HybridRetrievalEngine` **works**. The 0-candidate issue in the harness stems from a combination of a critical implementation bug in the BM25 retrieval engine and strict vocabulary constraints in the embedding model, which together result in a failure to map queries to indexed chunks.

## 2. Phase 1: Prune System Differential Matrix
The isolated prune matrix was reconstructed.
- `prune_data=False, prune_system=False` -> `PASS_CANDIDATES`
- `prune_data=True, prune_system=False` -> `PASS_CANDIDATES`
- `prune_data=False, prune_system=True` -> `PASS_CANDIDATES`
- `prune_data=True, prune_system=True` -> `FAIL_EMPTY_SEARCH` (Intermittent concurrency/locking Error 33 on Windows LadybugDB).

**Conclusion**: Calling `prune_system()` alone does **not** break Cognee. The previous failure was caused by state corruption/concurrency locks when both prune commands were run sequentially or concurrently on the same event loop in the harness.

## 3. Phase 2 & 3: Direct Cognee Retrieval Proof
Direct integration with `cognee.add()`, `cognee.cognify()`, and `cognee.search()` was successfully executed on the live fixtures.
- **Result**: `RETRIEVAL_SUCCESS`. `cognee.search()` successfully returned `ScoredCandidate` objects containing the expected text and external metadata (`canonical_document_id`, `trust_class`).
- **Proof Artifacts**: Log traces confirm "Found 4 chunks from vector search" during direct search.

## 4. Phase 4 & 5: Baseline Hybrid Retrieval Proof
The `HybridRetrievalEngine` was instantiated and tested outside the orchestrator.
- **BM25 Retrieval**: Fails unconditionally. A critical bug in `BM25Retriever._score` calculates term weights but fails to add them to the running `score` variable, explicitly returning `0.0` for all queries.
- **Vector Retrieval**: Succeeds only for queries whose vocabulary exactly matches the 7-word constraint in `SimpleEmbeddingModel` (e.g., "aspirin"). Queries without these exact tokens generate zero-vectors.
- **Result**: Because BM25 always returns 0.0 and vector search often returns 0.0 (due to vocabulary), the Reciprocal Rank Fusion (RRF) often yields 0 total candidates for standard medical queries.

## 5. Root Cause Classification
Based on the 11-phase diagnostic, the 0-candidate result is definitively classified as:
1. **RETRIEVAL_ENGINE_BUG**: The `BM25Retriever` implementation is mathematically broken and guarantees a 0.0 lexical score.
2. **RETRIEVAL_QUERY_ALIGNMENT_ISSUE**: The `SimpleEmbeddingModel` fails to map genuine semantic concepts outside its 7-word test vocabulary, yielding zero-vectors for the majority of Gate 5 queries.

The index is healthy. The mapping is correct. The engine logic and alignment layers are flawed.

## 6. Strict Directives & Next Steps
Per user instructions:
- **DO NOT** modify the security control logic.
- **DO NOT** change authorized Gate 5 case queries.
- **DO NOT** change authorized fixture content.
- **DO NOT** "optimize" the vocabulary to force a pass.

The harness and RAG pipeline are operating deterministically on flawed retrieval primitives. The next step is to address the `BM25Retriever` bug and establish a semantically capable embedding baseline before re-attempting Full Gate 5 execution.
