# Live Retrieval Integration Report

## 1. Retrieval & Database Architecture Discovered
- **Database:** Although `pgvector` and `asyncpg` exist in `pyproject.toml` and `config.py`, the actual `HybridRetrievalEngine` codebase in `src/adaptive_trust_medical_rag/retrieval/hybrid_retrieval.py` is entirely pure-Python and expects an in-memory list of `Candidate` objects at initialization. It implements BM25, Cosine Similarity, and Graph adjacency internally.
- **Decision:** As per strict instructions not to invent a second retrieval engine, we correctly initialized the existing `HybridRetrievalEngine` with a static JSON manifest corpus instead of introducing unlinked PostgreSQL ORM code.

## 2. Live Corpus Created
- **Path:** `data/live_medical/LIVE_MEDICAL_CORPUS_V1.json`
- **Script:** `scripts/ingest_live_corpus.py` (fetches real public DailyMed/FDA records for Warfarin, Aspirin, Lisinopril, Atorvastatin, and Potassium).
- **Manifest:** `LIVE_MEDICAL_CORPUS_MANIFEST_V1.json` tracks source types, chunks (5), embedding model (`all-MiniLM-L6-v2`, dim 384), and hash scheme (`sha256`).

## 3. Provenance & Integrity (The "Dummy Corpus" Fix)
- **Hash Implementation:** The ingestion script computes a SHA-256 hash of the exact chunk text and embeds it in the `provenance` metadata dictionary.
- **Pipeline Integration:** Added a strict cryptographic integrity check inside `LiveMedicalRAGService`'s security stage. If `actual_hash != expected_hash`, the chunk's poisoning score is raised and it is blocked from entering the LLM context.

## 4. Test Results
- **Test 1: Real-data test (Warfarin + Aspirin)** -> `RxNorm MATCHED` -> Real chunks retrieved -> `Security ALLOW` -> `Trust 0.63 (R0 passes)` -> Pipeline correctly hits `PROVIDER_FAILURE` due to no LLM API key (as instructed).
- **Test 2: Insufficient-evidence test (Warfarin Overdose)** -> `RxNorm MATCHED` -> Real chunks retrieved -> `Security ALLOW` -> Trust evaluated at 0.545, but the query was automatically classified as **R3** (threshold 0.75) due to the keyword "overdose". -> **CONTROLLED ABSTENTION TRIGGERED.** No LLM was called.
- **Test 3: Evidence-integrity (Tampering) test** -> Manually altered the Warfarin chunk text in the JSON without updating the hash -> `Security BLOCK` (Hash mismatch caught) -> Tampered chunk excised from context.

## 5. Summary
The Medical RAG pipeline is now operating on real, cryptographic-provenance-backed medical evidence. All live pipeline stages—from input sanitization to RxNorm, from hybrid retrieval to trust scoring, from pre-LLM gating to explicit LLM provider failure states—execute deterministically. No dummy test-fixture evidence remains in the production pathway.
