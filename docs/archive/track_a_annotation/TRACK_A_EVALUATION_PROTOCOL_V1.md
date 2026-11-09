# TRACK_A_EVALUATION_PROTOCOL_V1

## 1. Overview
The Track A Retrieval Evaluation measures the exact relevance and ranking quality of the biomedical evidence candidates produced by the baseline and Cognee retrieval paths. It strictly evaluates retrieval, decoupled from the generation and security layers.

## 2. Experimental Configurations

### Baseline Retrieval Configuration
- **Engine**: `HybridRetrievalEngine`
- **Embedding Model**: `S-PubMedBERT-MS-MARCO` (Frozen Authorized Revision)
- **Dimensionality**: 768
- **Pooling**: Mean pooling
- **Normalization**: L2 normalization
- **Similarity Measure**: Cosine similarity
- **Keyword Search**: BM25 Configuration (default parameters)
- **Rank Fusion**: Reciprocal Rank Fusion (RRF), `k=60`
- **Top-K**: 10
- **Corpus Version**: V2.0.0 (Amended)

### Cognee Retrieval Configuration
- **Engine**: Live `CogneeRetrievalAdapter`
- **Cognee Version**: 1.6.1
- **Search Type**: `SearchType.HYBRID` or equivalent chunks search
- **Embedding Configuration**: Same as baseline (`S-PubMedBERT-MS-MARCO`)
- **Top-K**: 10
- **Corpus Version**: V2.0.0 (Amended)
- **Provenance Mapping**: Retained natively via `external_metadata` tracking.

*Note*: The configurations ensure both systems operate on the identical underlying evidence universe and query targets.

## 3. Exclusion Rules
- Queries or positions lacking minimum sufficient context (e.g., missing abstracts that cannot be adjudicated) are flagged and documented in the dataset audit but are NOT silently dropped. 
- Synthetic prompt-injection documents (PI-01 through PI-10) are strictly excluded from the Track A corpus to prevent cross-contamination of research questions.
- The `SimpleEmbeddingModel` mock is strictly forbidden.

## 4. Execution Workflow
1. Freeze Annotation Schema & Protocol (Current Phase).
2. Human Annotation of 530 positions.
3. Adjudication of AMBIGUOUS and dual-annotated cases.
4. Final calculation of Recall@K, Precision@K, nDCG@K, and MRR per `TRACK_A_METRIC_DEFINITIONS_V1.md`.

## 5. Security & Isolation Guarantee
This protocol completely ignores Gate 5 outputs. Security decisions (e.g., `ELIGIBILITY_BLOCK`) are irrelevant to Track A, which evaluates the raw capabilities of the retrieval engines before safety thresholds are applied.
