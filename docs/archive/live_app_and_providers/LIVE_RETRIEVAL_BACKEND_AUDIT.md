# Live Retrieval Backend Audit

## Component Requirements

Based on an audit of `src/adaptive_trust_medical_rag/retrieval/hybrid_retrieval.py` and its dependencies:

1. **Retrieval Engine Architecture:**
   - The repository uses a pure-Python, in-memory `HybridRetrievalEngine` that implements three retrieval channels fused via Reciprocal Rank Fusion (RRF).
   - The channels are:
     - `BM25Retriever`: Exact entity mentions using an Okapi BM25 implementation.
     - `VectorRetriever`: Dense vector retrieval using normalized cosine similarity.
     - `GraphRetriever`: Knowledge graph relational retrieval using an adjacency list.
   - The engine expects to be instantiated with a pre-loaded list of `Candidate` objects (`corpus: list[Candidate]`) and a compliant `EmbeddingModel` protocol.

2. **Database & Vector Store Status:**
   - **Important finding:** Although `pyproject.toml` and `config.py` mention `pgvector`, `asyncpg`, and `sqlalchemy`, **there is currently no PostgreSQL/pgvector database code or ORM layer actually implemented** in the `src/` tree for retrieval.
   - The actual implemented retrieval logic completely delegates to in-memory list operations (`VectorRetriever` pre-encodes the corpus and computes cosine similarity on the fly).
   - Therefore, introducing a live PostgreSQL/pgvector connection now would require writing a completely new retrieval engine, which violates the strict rule: *"Do not implement a second retrieval engine."*

3. **Embedding Model:**
   - The system expects an implementation of the `EmbeddingModel` protocol (a class with a method `encode(self, texts: list[str]) -> list[list[float]]`).
   - The project includes `sentence-transformers` in its dependencies, which matches this interface easily.

4. **Chunk Representation:**
   - Uses the `Candidate` dataclass:
     ```python
     @dataclass(frozen=True)
     class Candidate:
         chunk_id: str
         document_id: str
         text: str
         source_url: str = ""
         source_authority: float = 0.5
         poisoning_score: float = 0.0
         metadata: dict = field(default_factory=dict, compare=False, hash=False)
     ```

5. **Provenance Requirements:**
   - Based on `RetrievalPoisoningDetector`, a valid chunk must have a cryptographic hash attached to its provenance metadata that matches the exact text.
   - Without this, the chunk gets a `poisoning_score` > 0.4 and is blocked.

## Architecture Decision for the Live Corpus
Since the required interface for `HybridRetrievalEngine` is purely in-memory, the "Live Evidence Store" for this vertical slice must be a structured JSON manifest (e.g., `data/live_medical/LIVE_MEDICAL_CORPUS_V1.json`). At application startup, the service will load this JSON into a list of `Candidate` objects and instantiate the engine. This exactly matches what the repository expects, introduces no orphaned PostgreSQL dependencies, and cleanly separates live data from the frozen historical benchmarks.
