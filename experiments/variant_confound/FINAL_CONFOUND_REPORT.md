# Final Confound Report (GATE 12)

**Status:** CONFOUND_RESOLVED
**Date:** 2026-09-12

## 1. Original Confound
The original evaluation architecture (live_variants.py and ablation_runner.py) conflated multiple system changes between the experimental variants (B, C, D, E) and the full system (F). Most notably, Variant B (the baseline) used a naive single-document corpus and a dense-only retrieval mock, while Variant F used the 4-document manifest.json corpus and a full multi-channel Hybrid Retrieval pipeline (top_k=10). 

## 2. Source of Confound
In live_variants.py, variants B through E were implemented using _make_default_corpus() (which returned a hardcoded single Candidate) and invoked retriever.retrieve(..., top_k=5).
Variant F, routed through AdaptiveTrustRAGOrchestrator, used load_evidence_corpus() (which dynamically loaded 4 candidates from data/evidence/manifest.json) and invoked retrieval with request.top_k defaulting to 10.

## 3. Code Correction
1. Unified _make_default_corpus() to return load_evidence_corpus(), ensuring all variants operate on the same 4-document underlying dataset.
2. Updated live_variants.py to enforce top_k=10 across Variants B, C, D, and E to match Variant F.
3. Fixed retrieval_execution metadata logging in B, C, D, and E to correctly report bm25_called=True and graph_called=True.
4. Statically patched live_variants.py so all variants explicitly call the same _normalize_query_sync() pipeline and pass the same query_drugs list to the HybridRetrievalEngine.

## 4. Configuration Equality
Computed configuration hashes (compute_config_hashes.py) confirmed that the underlying Corpus hash, Retrieval Engine configuration hash (BM25 params, embeddings), and Ranking configuration hash (RRF) are now mathematically identical across Variants B, C, D, E, and F.

## 5. Retrieval Equality
Test file tests/test_variant_retrieval_equivalence.py was introduced, simulating the exact retrieval pipelines for variants B, C, D, and E across 3 benchmark queries. The tests verify that all 4 variants produce the **identical candidate chunk IDs**.

## 6. Evidence-Pack Equality
The tests also verified that the RRF final_rank ordering, the returned candidate list length, the exact RRF scores (to 10 decimal places), and the concatenated context_text are strictly identical.

## 7. Intended Experimental Differences
The only remaining differences between the baseline (B) and the security evaluations (D, E, F) are:
- Variant D: Prompt-level injection of normalized entities.
- Variant E: Application of AdaptiveTrustScorer and dropping candidates below the risk-tier threshold (0.45 default).
- Variant F: Full dual safety gates (Evidence Eligibility Gate + Answer Safety Gate) and dynamic NLI contradiction checks.

## 8. Remaining Differences
Variant B uses "Context:" as the prompt header, while E uses "Trust-Scored Evidence Context:". This is a cosmetic prompt prefix difference necessary for the respective treatments.

## 9. Test Evidence
- **Retrieval Equivalence**: 38 tests passed in test_variant_retrieval_equivalence.py.
- **Live Variant Metadata**: 17 tests passed in test_live_variants.py.
- **Full Regression**: 806 tests passed in tests/.
- **Security Scans**: bandit identified 13 known test/mock-related Lows; gitleaks identified 1 known intentional mock API key test fixture.

## 10. Phase 15 Impact
**Classification**: NO_IMPACT
The Phase 15 log remains empty, the test split is completely unexecuted, and the phase15_cases.jsonl SHA-256 hash has not changed. The structural corrections isolated to Phase 14.7 architecture will ensure that when Phase 15 is executed, the measurements will accurately reflect the security treatment without retrieval pipeline confounding.
