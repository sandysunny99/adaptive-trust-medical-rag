# Phase 2A: TOY-CORPUS BASELINE Report (v1)

## 1. Actual Retrieval Architecture
- **Current Retriever**: `HybridRetrievalEngine`
- **Algorithms Used**: 
  - **Lexical**: Okapi BM25 (`k1=1.5`, `b=0.75`) via pure-Python `BM25Retriever`.
  - **Dense**: Cosine similarity via `VectorRetriever`.
  - **Graph**: Max 2-hop BFS on hardcoded severity heuristics (`GraphRetriever`).
  - **Fusion**: Reciprocal Rank Fusion (RRF) with `k=60`.

## 2. Verified Embedding Configuration (Code Audit Finding)
- **Actual Embedding Model**: The live orchestrator passes `SimpleEmbeddingModel` (verified from code).
- **Implementation**: The current dense retriever is implemented using a 7-dimensional deterministic toy encoder using a hardcoded vocabulary (`["metformin", "aspirin", "warfarin", "dosage", "mechanism", "renal", "indication"]`).
- **Persistence**: Re-calculated entirely in-memory at runtime. 

## 3. Current Corpus (Toy Benchmark)
- **Size**: 4 documents manually curated for the frozen baseline (`chunk-metformin-001`, `chunk-warfarin-001`, `chunk-haloperidol-001`, `chunk-spironolactone-001`).

## 4. Ground Truth
- **Dataset**: Evaluated on the 20-case frozen smoke dataset (`live-smoke-v1`).
- **Curation**: Only 3 cases had relevant evidence present in the 4-document corpus. The other 17 cases were strictly labelled `NO_GROUND_TRUTH_EVIDENCE`.

## 5. R0-R3 Empirical Baseline Results (Experimental Finding)
The following metrics were calculated from `case_results.jsonl` strictly on the 3 valid ground-truth cases.

- **R0 (BM25 Only)**: `Recall@5: 1.0`, `MRR: 0.833`.
- **R1 (Dense Only)**: `Recall@5: 1.0`, `MRR: 1.0`. 
- **R2 (BM25 + Dense)**: `Recall@5: 1.0`, `MRR: 1.0`.
- **R3 (Hybrid + Graph)**: `Recall@5: 1.0`, `MRR: 1.0`.

## 6. Recommended Next Upgrade
**Decision Gate**: 
R0-R3 were successfully executed. However, the corpus and relevance labels are insufficient for evaluating semantic retrieval quality. The current dense retriever is implemented using a 7-dimensional deterministic toy encoder, and the existing benchmark is insufficient to evaluate genuine semantic retrieval.

The next step is NOT to immediately choose PubMedBERT, SapBERT, or MedCPT.
The next step is **Phase 2B.1: Build a larger biomedical retrieval evaluation benchmark (100-500 documents)** with independently curated ground truth, domain-stratified queries, and lexical variation (synonyms/paraphrases) that can actually distinguish between Lexical, Dense, and Graph retrieval performance.