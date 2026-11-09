# OPTION A SUBOPTION ANALYSIS V2

**Date:** 2026-10-03  

Option A (Imputation) must be split into two fundamentally different approaches.

## A1: Direct Retrieval-Score Imputation
**Mechanism:** Imputing `query_relevance` using the score provided by the retrieval engine (e.g., BM25 score, LanceDB cosine similarity, or Cognee/RRF ranking).
- **Circularity:** `Retrieval Engine Output -> Trust Score -> Eligibility -> Generation`.
- **Score Normalization Problem:** BM25 produces unbounded scores. Cosine is `[-1, 1]`. RRF is `(0, 1]`. These cannot be safely mapped to a continuous `[0, 1]` trust factor without engine-specific scaling.
- **Benchmark Comparability:** **INVALIDATED.** A candidate chunk might pass eligibility under Baseline but fail under Cognee strictly because the graph retrieval math scales differently than vector math, confounding the hallucination evaluation.
- **Verdict:** Methodologically highly problematic.

## A2: Engine-Independent Relevance Measurement
**Mechanism:** Imputing `query_relevance` using an independent evaluator that runs *after* retrieval (e.g., a cross-encoder or an LLM-as-a-judge comparing the chunk to the query).
- **Circularity:** Avoided. `Retrieval -> Independent Measurement -> Trust -> Eligibility`.
- **Candidate Measurement Mechanisms:** 
  - Cross-encoder: Referenced in architecture (`MedCPT`), but not currently implemented or wired as an independent trust scorer.
  - LLM Evaluator: Not implemented for this purpose.
- **Evidence Quality Measurement:** Still unresolved. Even if `query_relevance` is solved by A2, `evidence_quality` (10-25% of score) still requires a separate metadata/independent signal.
- **Methodology Impact:** Valid, but requires building and integrating new measurement modules.
- **Rerun Requirement:** YES. Gate 5 must be entirely rerun.

## Conclusion
A1 introduces invalid circularity. A2 is scientifically valid but constitutes a significant pipeline expansion (new modules) and still does not solve `evidence_quality` imputation.
