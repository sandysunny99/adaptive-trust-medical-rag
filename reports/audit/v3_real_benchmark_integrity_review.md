# V3 Real Benchmark Integrity Review

## Status
**V3_REAL_PIPELINE_RUN**
**STATUS = DIAGNOSTIC_ONLY**
**FINAL_CONFIRMATION = INVALID**

## Reason
While the corpus was constructed from real biomedical literature fetched from PubMed, the relevance labels were still generated algorithmically from lexical term co-occurrence rather than independently curated at the document/chunk level. 

Specifically, the ground-truth logic required the drug and a related keyword to be present in the abstract for it to be labeled `DIRECT_SUPPORT`. This automated lexical rule intrinsically favored the BM25 baseline.

Furthermore, out of 80 cases, 55 were created by taking the original 25 queries and appending templated suffixes (e.g., "in clinical settings") while reusing the same ground-truth documents. This violated the requirement for independently constructed evaluation cases.

## Impact
Because the benchmark was lexically biased, the `F0` baseline achieved `Recall@5 = 1.000`, leaving no room for the cross-encoder to demonstrate semantic improvement. The slight drop in MRR@20 (p=0.837) merely shows statistical non-significance under a lexically biased condition, not definitive proof of safety or equivalence. 

Therefore, the benchmark is not suitable as final confirmation evidence for semantic retrieval or reranking superiority.

## Next Steps
A `v3.1` benchmark will be created using the existing 248-document corpus. It will feature 60-100 independently authored, non-templated evaluation cases. Relevance annotations will include exact evidence spans, hard negatives will be deliberately identified, and authority metadata will be preserved without assuming all PubMed results are equivalent to FDA labels.