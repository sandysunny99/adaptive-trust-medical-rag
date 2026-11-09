# OPTION A: SIGNAL VALIDITY ANALYSIS (IMPUTATION)

**Date:** 2026-10-03  
**Proposal:** Impute `query_relevance` from existing retrieval signals (e.g., BM25 score, RRF, or vector cosine similarity).

## 1. Candidate Signal Analysis

| Signal | Bounded? | Normalized? | Engine-Dependent? | Comparable across engines? |
|---|---|---|---|---|
| **BM25 Score** | No (Unbounded) | No | Yes | No |
| **Vector Cosine Sim.** | Yes `[-1, 1]` | Yes | Yes | No |
| **RRF Score** | Yes `(0, 1]` | Yes | Yes (Rank-dependent) | No |

## 2. The Circularity Risk (CRITICAL)

The core research objective of this RAG pipeline relies on evaluating hallucination reduction using an **independent Trust Layer**. The experiment directly compares the Baseline (BM25 + Vector) against the Cognee (Graph) retrieval engine.

If `query_relevance` (20% of the R1 trust score) is derived from the retrieval engine's score:
1. **Dependency:** `Retrieval Engine Math → Trust Score → Evidence Eligibility`.
2. **Contamination:** BM25 and Vector models output fundamentally different score distributions than a Graph engine.
3. **Confounding Variable:** A candidate might pass eligibility under the Baseline but fail under Cognee *purely because of the mathematical scaling of the retrieval engine*, not because the evidence is scientifically less trustworthy.

## 3. Conclusion

**Factually Established:** Using retrieval scores in the trust formula creates circularity, making Trust retrieval-dependent. This scientifically invalidates the Baseline vs Cognee comparability. Option A introduces severe methodological contamination to the core research benchmark.
