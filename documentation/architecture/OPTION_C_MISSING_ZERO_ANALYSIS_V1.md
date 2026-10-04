# OPTION C: MISSING=ZERO ANALYSIS

**Date:** 2026-10-03  
**Proposal:** Keep defaults at `0.0`.

## 1. Fail-Closed vs Measurement Deficiency

- **Measurement Deficiency:** The architecture penalizes candidates strictly because the pipeline currently lacks the instrumentation to measure `query_relevance` and `evidence_quality` outside of the retrieval engine (e.g., using a cross-encoder reranker which is listed as Conceptual/MedCPT but unintegrated).
- **Conservative Behavior:** Because the instrument is missing, the trust score is artificially depressed by 30-35%. 
- **Fail-Closed:** This creates an inherently conservative (fail-closed) posture. The system refuses to extend trust when it lacks measurement data.

## 2. Consequences

- **Historical Reproducibility:** PERFECT. Requires zero reruns. Gate 5 is preserved exactly.
- **R3 Reachability:** IMPOSSIBLE. The `0.65` ceiling locks out the R3 threshold (`0.75`).
- **Research Claims:** The thesis methodology must explicitly document this limitation: *"Due to a lack of independent relevance/quality instrumentation, the continuous trust score operates conservatively (missing=0.0). Consequently, the R3 risk tier (High-Risk/Lethal) is mathematically inoperable and triggers controlled abstention by default."*
