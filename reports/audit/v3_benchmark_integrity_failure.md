# V3 Benchmark Integrity Failure

## Status
**INVALID_FOR_FINAL_CONFIRMATION**

## Reason
Synthetic documents were generated directly from evaluation cases. The V3 construction script explicitly created one synthetic document per evaluation query, encoding the lexical terms of the query directly into the document string, and then algorithmically derived the ground-truth relevance from those same terms. This established a direct query-to-document construction leakage.

## Impact
Because the corpus was lexically aligned with the query by design, the `F0` (BM25) baseline artificially achieved a perfect `Recall@5 = 1.000`. Consequently, the V3 benchmark cannot establish general retrieval superiority, nor can it demonstrate that MedCPT resolves hard ranking inversions (since none were possible in the synthetic corpus). 

## Use
This synthetic V3 benchmark run may be retained exclusively as a diagnostic pipeline/infrastructure test. It is strictly prohibited from being used as a final research result or a justification for production integration.

## Correction Plan
A new `retrieval-v3-real` benchmark will be constructed using authentic biomedical evidence (PubMed/DailyMed) acquired via broad topic queries (C-SET) that are distinct from the final evaluation queries (E-SET). Ground truth will be independently curated, chunked, and frozen before retrieval evaluation.