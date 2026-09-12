# Final Confound Report (GATE 12)

**Status:** CONFOUND_RESOLVED
**Date:** 2026-09-12

## 1. Variant A (Vanilla LLM) Separation
Variant A is kept strictly separate from the B-F ablation variants. Variant A acts as a zero-RAG hallucination baseline, but is **NOT** the baseline for the security effect. Variant B is the primary baseline for assessing the security architecture.

## 2. Original Confound
The original evaluation architecture conflated multiple system changes between the experimental variants (B, C, D, E) and the full system (F). Most notably, Variant B (the baseline) used a naive single-document corpus and a top-k of 5, while Variant F used the 4-document manifest.json corpus and top_k=10.

## 3. Retrieval Equivalence (B/C/D/E/F)
All variants (B, C, D, E, F) now execute the mathematically identical underlying retrieval pipeline. 
- **Query Normalization:** All use the same normalization resolving to the same query_drugs.
- **Corpus:** All variants retrieve from load_evidence_corpus() (4 documents).
- **Parameters:** All variants use 	op_k=10 and identical BM25/Dense/Graph parameters.
- **Evidence Pack:** All variants produce identical initial candidate IDs, ordering, and RRF scores.

## 4. Intended Experimental Differences (Treatment)
The remaining differences between the baseline (B) and the security evaluations are strictly intentional experimental treatments:
- **B ? D**: Effect of explicit entity-awareness in the prompt on the LLM's adherence to the correct drug.
- **B ? E**: Effect of adaptive trust-aware pre-generation evidence gating on hallucination and misattribution rates.
- **B ? F**: Effect of the full dual-gate security and verification architecture on end-to-end safety and abstention rates.

## 5. Phase 15 Impact
**Classification**: NO_IMPACT
The Phase 15 log remains empty, the test split is completely unexecuted, and the phase15_cases.jsonl SHA-256 hash has not changed (f71c70d36081b1b68316b5ff8636969c8b964c9655f752b41112694ebc02c48).
