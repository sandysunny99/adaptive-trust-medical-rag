# Baseline Semantic Model Authorization Decision Package V1

## Final Status: `S_PUBMEDBERT_HISTORICAL_CANDIDATE_AUTHORIZATION_REQUIRED`

The historical candidate has been identified (`pritamdeka/S-PubMedBert-MS-MARCO`), but formal protocol authorization is still pending. Full Gate 5 remains stopped.

---

## Final Questions Answered

### 1. What exact document defines the Gate 5 dense baseline?
**No single normative protocol document defines it.** `FREE_REPLICATION_V1_PROTOCOL.md` defines the LLM generation constraints but is silent on the embedding model. `docs/ARCHITECTURE.md` defines the database schema constraint (`VECTOR(768)`). `CURRENT_ARCHITECTURE_SNAPSHOT.md` describes the current implementation state but does not prescribe the baseline.

### 2. Does that document name an embedding model?
No. `docs/ARCHITECTURE.md` does not name a model, it only specifies a dimension (768). The only documents that explicitly name a model are historical experiment manifests (e.g., `fusion-evaluation-v3-real/manifest.json`).

### 3. Is SimpleEmbeddingModel normative or merely descriptive/current implementation?
**It is merely descriptive/current implementation.** It was introduced on Aug 23 as a testing mock to replace an ablation engine. It only appeared in `CURRENT_ARCHITECTURE_SNAPSHOT.md` because that snapshot was a point-in-time capture of the codebase, not an authorization protocol.

### 4. Was S-PubMedBert actually used as a historical baseline, or only as an experiment model?
**It was the primary experimental dense model.** It was introduced via `RealEmbeddingModel` on Sep 11 and used in 11+ experiment scripts (e.g., `run_fusion_evaluation.py`) to generate the base dense candidates (F0) before cross-encoder reranking. It served as the semantic baseline against which other biomedical models (like `SapBERT`) were evaluated.

### 5. Why does the architecture specify VECTOR(768)?
The `VECTOR(768)` specification was introduced in `docs/ARCHITECTURE.md` on Aug 23, *before* `S-PubMedBert` was introduced on Sep 11, and hours *before* `SimpleEmbeddingModel` was created. 768 is the standard dimension for BERT-base models. It was chosen as a standard architecture placeholder, making the database natively compatible with `S-PubMedBert`, but it does not formally mandate that specific model over other 768-dim models.

### 6. What prior experiments are genuinely comparable to S-PubMedBert?
The `fusion-evaluation-v3-real` and `fusion-evaluation-v3-confirmed` experiments are fully comparable, as their manifests explicitly record using `S-PubMedBert-MS-MARCO`. Conversely, `retrieval-baseline-v1` and early `FREE_REPLICATION_V1` tests that relied on the orchestrator's default `SimpleEmbeddingModel` are **not comparable**.

### 7. What protocol amendment is required, if any?
An explicit protocol amendment is required to:
1. Formally authorize `pritamdeka/S-PubMedBert-MS-MARCO` as the Gate 5 dense baseline.
2. Invalidate prior `FREE_REPLICATION` tests that inadvertently used the 7-dim test fixture.

### 8. What exact decision must be frozen before Full Gate 5?
The research lead must decide: **"Is `pritamdeka/S-PubMedBert-MS-MARCO` the authorized dense embedding model for Gate 5?"** Once decided, the exact HuggingFace revision hash and offline provisioning mechanism must be frozen in the configuration.

### 9. Which evidence is runtime-captured and which is documentary/historical?
*   **Runtime-captured:** The V2 and V4 diagnostic artifacts (`RUNTIME_EVIDENCE_PROVENANCE_V4.md`, `MODEL_CHARACTERIZATION_RUNTIME.jsonl`) which serialize direct live return values (candidate counts, vector dimensions).
*   **Documentary/Historical:** The commit histories, architecture snapshots, and `manifest.json` files from prior experiment runs. All have been strictly segregated in the analysis.

### 10. Is the project now ready to select/freeze a baseline, or is another protocol source still missing?
**The project is ready to select and freeze the baseline.** We have exhausted all internal documentary evidence. The historical usage is clear, the current implementation's flaws are proven, and the comparability impact is mapped. The only missing piece is the formal human authorization decision to adopt the historical candidate.

`evidence_source`: `manual_analysis`
