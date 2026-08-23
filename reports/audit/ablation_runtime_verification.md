# Ablation Variant Runtime Architectural Verification

| Variant | Name | Retrieval Mechanism | Entity Normalization | Trust Scoring | Pre-Gen Gate | Answer Safety Gate | Abstention Mechanism |
|---------|------|---------------------|----------------------|---------------|--------------|--------------------+----------------------|
| **A** | Vanilla LLM | None | No | No | No | No | No |
| **B** | Dense RAG | Dense Vector ($k=5$) | No | No | No | No | No |
| **C** | Hybrid RAG | Dense + BM25 RRF | No | No | No | No | No |
| **D** | Entity RAG | Dense + Graph | Yes (RxNorm) | No | Yes | No | Partial |
| **E** | Trust RAG | Dense + BM25 | Yes (RxNorm) | Yes ($T_{\text{chunk}}$) | Yes | No | Yes (R0-R3) |
| **F** | **Full Arch** | Hybrid + Graph | Yes (RxNorm) | Yes ($T_{\text{chunk}}$) | **Yes** | **Yes** | **Yes (R0-R3)** |

**Verification Status:** Runtime capabilities verified across variants A through F.
