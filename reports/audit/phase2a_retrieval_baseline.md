# Phase 2A: Retrieval Audit and Baseline Design

## 1. Existing Retrieval Architecture Audit

**Current Engine:** `HybridRetrievalEngine`
**Channels:** BM25 (Lexical), Vector (Dense Semantic), Graph (Entity Traversal).
**Fusion Method:** Reciprocal Rank Fusion (RRF) with `k=60`.

### A. Inventory of Retrieval Stages
1. **Query Construction:** Free-text clinical query optionally augmented with normalized drug names via RxNorm.
2. **Parallel Retrieval:**
   - **Lexical (`BM25Retriever`):** TF-IDF/BM25 keyword matching against candidate chunks.
   - **Semantic (`VectorRetriever`):** Dense vector similarity (cosine) against candidate embeddings.
   - **Graph (`GraphRetriever`):** 2-hop BFS traversal for DDI/ADE queries across known drug relationships (e.g. `contraindicated`, `severe`, `moderate`).
3. **Fusion & Reranking:** Multi-channel results are fused via RRF (`1 / (60 + rank)`).
4. **Pre-generation Filtering:** Candidates with `poisoning_score > 0.4` are explicitly filtered.

### B. Identified Weaknesses in Current Baseline
- **Embedding Model:** Currently depends on generic LLM-based embeddings via the default model adapter. It lacks deep biomedical nuance for complex pharmacology pathways.
- **Trust Integration:** `TrustScorer` operates primarily as a post-retrieval validation gate rather than influencing the initial retrieval ranking (trust scores do not currently weigh into RRF).
- **Metadata Filtering:** No hard filtering for evidence source tiers (e.g., forcing FDA labels for overdose/lethal dose queries) during the vector search phase.

## 2. Phase 2 Baseline Evaluation Design

Before upgrading components, we will evaluate the current retrieval mechanism using frozen case-level evaluation data on DDI, ADE, and Pharmacology queries.

**Metrics to Capture:**
- `Recall@k` (Are the key factual chunks retrieved in the top K?)
- `Precision@k` (What proportion of retrieved chunks are clinically relevant?)
- `MRR` (Mean Reciprocal Rank of the first highly relevant evidence chunk)

**Ablation Variants (Retrieval Isolation):**
- **R0:** Lexical-only baseline (disable Vector & Graph).
- **R1:** Dense-only baseline (disable BM25 & Graph).
- **R2:** Hybrid (Lexical + Dense, no Graph).
- **R3:** Full Hybrid (Current State: Lexical + Dense + Graph).
- **R4:** Hybrid + Trust-aware reranking (Phase 2 Upgrade).

## 3. Next Steps (Phase 2 Implementation)
1. **Develop Retrieval Evaluation Harness:** Build an isolated evaluation suite to calculate `Recall@k` and `MRR` strictly for the retrieval engine (bypassing the generation layer).
2. **Execute Frozen Baseline Experiment:** Measure R0 through R3 on the existing smoke test dataset.
3. **Analyze Error Cases:** Identify specific clinical interactions (e.g., CYP450 metabolism interactions) where semantic search currently fails.
4. **Select Specialized Embeddings:** Evaluate PubMedBERT, SapBERT, or MedCPT based on the error case analysis to improve the dense retrieval channel.