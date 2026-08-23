# Ablation Execution Forensics & Runtime Audit

**Audit Status:** `FORENSIC AUDIT COMPLETE — MOCK ENGINE ISOLATED & REAL LIVE BACKEND SPECIFIED`

## 1. Executive Summary & Critical Findings

A forensic audit of the evaluation codebase revealed that historical ablation benchmarks were executed via `MockVariantPipeline` (in `evaluation/ablation_runner.py`), which uses pre-configured statistical profile distributions to simulate LLM and retrieval outputs. While effective for deterministic CI smoke testing (6.9 ms/case execution time), **these simulated metrics do not constitute paper-publication live research evidence**.

To achieve academic validity, the live evaluation pipeline (`medical-rag research-run --mode live`) has been decoupled from simulation stubs and wired to execute real RAG pipeline components via `evaluation/live_variants.py`.

---

## 2. Variant-by-Variant Execution Tracing

| Variant | Name | Real Execution Class | Real Retrieval Backend | Real Entity Normalization | Real Trust Scoring | Real LLM Invocation | Real Safety Gates |
|---------|------|----------------------|------------------------|---------------------------|--------------------|---------------------|-------------------|
| **A** | Vanilla LLM | `RealVariantA` | None | None | None | `ContextGroundedLLM` | None |
| **B** | Dense RAG | `RealVariantB` | `HybridRetriever` (Dense vector only) | None | None | `ContextGroundedLLM` | None |
| **C** | Hybrid RAG | `RealVariantC` | `HybridRetriever` (BM25 + Dense RRF) | None | None | `ContextGroundedLLM` | None |
| **D** | Entity RAG | `RealVariantD` | `HybridRetriever` (Hybrid + Graph) | `DrugEntityNormalizer` (RxNorm) | None | `ContextGroundedLLM` | Pre-Gen Eligibility (Partial) |
| **E** | Trust RAG | `RealVariantE` | `HybridRetriever` (Hybrid + Graph) | `DrugEntityNormalizer` (RxNorm) | `TrustScorer` ($T_{\text{chunk}}$) | `ContextGroundedLLM` | Pre-Gen Eligibility Gate (R0-R3) |
| **F** | **Full Arch** | `RealVariantF` (`RAGOrchestrationEngine`) | `HybridRetriever` (Hybrid + Graph RRF) | `DrugEntityNormalizer` (RxNorm) | `TrustScorer` ($T_{\text{chunk}}$) | `ContextGroundedLLM` | **Dual Gates** (Eligibility + Answer Safety) |

---

## 3. Real Execution Verification Protocol

Each live evaluation case records explicit, un-mocked runtime execution provenance in `case_results.jsonl`:

- `"execution_backend": "live_real_pipeline"`
- `"runtime_verified": true`
- `"llm_execution"`: `{ "called": true, "provider": "google-genai", "model": "gemini-2.5-flash", "latency_ms": ... }`
- `"retrieval_execution"`: `{ "dense_called": true, "bm25_called": true, "graph_called": true, "rrf_called": true, "retrieved_count": ... }`
- `"trust_execution"`: `{ "called": true, "weights": {...}, "threshold": ..., "accepted_chunks": ..., "rejected_chunks": ... }`
- `"verification_execution"`: `{ "called": true, "claim_count": ..., "supported": ..., "unsupported": ..., "contradicted": ... }`
- `"query_hash"`: `sha256(actual_user_query.encode())` (computed dynamically from the actual input query).
