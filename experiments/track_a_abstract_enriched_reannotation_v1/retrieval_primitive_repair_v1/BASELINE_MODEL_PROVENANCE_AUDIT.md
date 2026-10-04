# BASELINE MODEL PROVENANCE AUDIT

## 1. Intentionality of SimpleEmbeddingModel
Based on the project's commit history and architectural documentation, `SimpleEmbeddingModel` is **not** an intentionally specified semantic baseline. It is a temporary engineering/testing fixture.

## 2. Provenance Timeline
* **August 23, 2026 (Commit `ea97355`):** `SimpleEmbeddingModel` was introduced as a mock in `live_variants.py` to replace a mock ablation engine with the initial real-live execution pipeline. Its vocabulary was restricted to 7 words (`["metformin", "aspirin", "warfarin", "dosage", "mechanism", "renal", "indication"]`).
* **September 13, 2026 (Commit `ed3cf9c`):** The model was left in place during testing of the variant retrieval equivalence proof.
* **September 13, 2026 (Commit `b18461d`):** `CURRENT_ARCHITECTURE_SNAPSHOT.md` was created to document Phase 14.5 guardrail evaluation protocols. During this documentation phase, `Dense (SimpleEmbeddingModel)` was accidentally promoted into the snapshot as the dense channel, reflecting the *current state of the code* rather than the *authorized research protocol*.
* **Protocol Documents:** Neither `FREE_REPLICATION_V1_PROTOCOL.md` nor `FREE_REPLICATION_V1_CONFIG.json` explicitly authorize `SimpleEmbeddingModel`. Furthermore, `pyproject.toml` lists `sentence-transformers>=6.0.1` as a Phase 10 dependency, indicating a true semantic model was intended to be used.

## 3. Conceptual Distinctions
* **A. CURRENT IMPLEMENTATION:** `SimpleEmbeddingModel` (a 7-word mock).
* **B. AUTHORIZED RESEARCH BASELINE:** Unspecified. The architectural snapshot merely captured the temporary test fixture state. The protocol never explicitly authorized it.
* **C. SEMANTICALLY REALISTIC BASELINE:** A production embedding model (such as BAAI/bge-small-en-v1.5) that uses `sentence-transformers`, which is listed in the dependencies but not implemented in the baseline retrieval path.

## 4. Conclusion
**MODEL_IS_TEST_FIXTURE_NOT_AUTHORIZED**
The current implementation relies on a test fixture that was unintentionally recorded as the baseline. The true authorized semantic baseline is unspecified.

`evidence_source`: `manual_analysis`
