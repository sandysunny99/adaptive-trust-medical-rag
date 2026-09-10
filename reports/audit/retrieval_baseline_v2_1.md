# Phase 2B.2: Valid Retrieval Benchmark Results (v2.1)

## 1. Experimental Setup
- **Corpus**: V2.1 Frozen Biomedical Corpus (77 documents)
- **Evaluation Set**: 19 completely held-out queries (6 positive evidence cases)
- **Methodology**: Queries used for corpus acquisition were strictly separated from the evaluation queries. Ground truth was assigned by semantic intersection, preventing the exact-keyword bias present in the v1 baseline.

## 2. Overall Performance Metrics (Recall@5 & MRR)
Calculated strictly on the 6 independent positive-evidence cases.

- **R0 (BM25 Only)**: `Recall@5: 0.667`, `MRR: 0.500`
- **R1 (Dense Only - Toy Encoder)**: `Recall@5: 0.000`, `MRR: 0.000`
- **R2 (BM25 + Dense)**: `Recall@5: 0.667`, `MRR: 0.500`
- **R3 (Hybrid + Graph)**: `Recall@5: 0.667`, `MRR: 0.500`

## 3. The Semantic Retrieval Bottleneck (Final Diagnosis)
The corrected benchmark decisively answers the core research question regarding the current dense implementation:

**Does the 7-dimensional deterministic toy encoder help on paraphrased, mechanistic, or synonym queries?**
**No.** R1 (Dense) dropped from 1.0 (in the contaminated v1 benchmark) to **0.000** in the uncontaminated v2.1 benchmark. The 7-word hardcoded vocabulary (`metformin`, `aspirin`, `warfarin`, `dosage`, `mechanism`, `renal`, `indication`) catastrophically fails when evaluated on held-out semantic queries (e.g., "potassium-related adverse effect" instead of "hyperkalemia spironolactone").

**Does Hybrid (R2/R3) outperform BM25 (R0)?**
**No.** Because the dense channel returns irrelevant noise (or nothing) for queries outside its 7-word vocabulary, RRF (Reciprocal Rank Fusion) provides no measurable lift over pure BM25. 

## 4. Decision Gate Outcome
**EMPIRICAL FINDING**: The current dense retrieval channel is entirely incapable of semantic retrieval on held-out paraphrased and synonym queries, scoring 0.000 Recall@5.

**Decision: CASE A (Semantic retrieval is genuinely weak).**
The project must now proceed to **Phase 2C: Biomedical Embedding Evaluation**. We must replace `SimpleEmbeddingModel` with a legitimate dense encoder (e.g., PubMedBERT, SapBERT) and rerun this exact R0-R3 evaluation to restore the semantic capabilities of the RAG pipeline.