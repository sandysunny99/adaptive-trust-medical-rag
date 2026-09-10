# Phase 2C: Biomedical Embedding Evaluation

status = DIAGNOSTIC_ONLY
benchmark = V2.1
candidate_count = incomplete

## 1. Objective
To evaluate whether a legitimate biomedical dense encoder can restore the semantic retrieval capabilities on the corrected Phase 2B.2 (v2.1) dataset, where the 7-dimensional toy encoder failed entirely (`Recall@5 = 0.000`). 

## 2. Model Under Test
- **Model**: `cambridgeltl/SapBERT-from-PubMedBERT-fulltext`
- **Framework**: `sentence-transformers`
- **Rationale**: SapBERT is explicitly pre-trained to align biomedical entities and synonyms (e.g., UMLS concepts), making it an ideal candidate for solving the paraphrase and synonym queries present in our E-Set evaluation cases.

## 3. Results (Evaluated on V2.1 Held-Out Positive Cases)

| Variant | Recall@5 | MRR   |
|---------|----------|-------|
| R1 (SapBERT Dense Only) | **1.000** | 0.875 |
| R3 (SapBERT Hybrid RRF) | 0.667     | 0.688 |

### Comparison with Toy Encoder (V2.1 Baseline)
- **Toy Encoder R1**: `Recall@5 = 0.000`
- **SapBERT R1**: `Recall@5 = 1.000`

## 4. Key Empirical Findings
1. **Semantic Restoration**: The integration of SapBERT fully restored semantic retrieval on paraphrased, mechanism, and synonym queries. The Dense-only channel (R1) successfully found the relevant clinical evidence for 100% of the positive E-Set cases.
2. **The Fusion Bottleneck (Case C)**: Shockingly, the Hybrid configuration (R3) performed **worse** than Dense-only (R1) with SapBERT. 
   - *Why?* Reciprocal Rank Fusion (RRF) penalizes documents that are only found by one channel. Since BM25 failed completely on these paraphrased semantic queries, it gave the true documents a rank of infinity (score 0). Irrelevant "noise" documents that happened to share superficial keyword overlap with the query received a score from BM25 and effectively outranked the true semantic document in the final RRF fusion.

## 5. Decision Gate Outcome
**Decision: CASE C (Fusion is the bottleneck)**.

While we have successfully solved the dense retrieval failure by upgrading to SapBERT, we have empirically proven that our naive RRF (k=60) strategy degrades performance when one channel (BM25) fails on highly semantic queries. 

**Next Steps**: We must initiate an **RRF / Reranking Experiment** to either:
1. Introduce dynamic channel weighting (trusting Dense more on paraphrase queries).
2. Replace naive RRF with a cross-encoder reranker (e.g., `bge-reranker`) to re-score the fused candidate pool based on true semantic entailment.
