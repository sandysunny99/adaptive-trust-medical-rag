# Architecture

This document describes the code as of commit `9bae325` (2026-10-18). Section 1 is the live application that the browser frontend uses and section 2 its two safety gates. Section 5 is the research harness (CLI, ablation variants, database schema), a separate path. Section 8 lists where this document differs from its earlier version.

## 1. Live application pipeline

Entry points (FastAPI, `src/adaptive_trust_medical_rag/api/routes/analyze.py`, prefix `/api/v1`):

| Endpoint | Purpose |
|---|---|
| `GET /api/v1/llm/models` | Model catalog with availability (from `llm_backend/model_registry.py`) |
| `POST /api/v1/analyze` | Start an analysis from drug names (JSON: names, optional `patient_context`, optional `additional_instructions`, optional `llm_selection`) |
| `POST /api/v1/analyze/prescription` | Start an analysis from a prescription image (multipart) |
| `POST /api/v1/analyze/{request_id}/confirm` | Confirm the extracted medications (medication objects only; plain strings are rejected with 422) |
| `GET /api/v1/stream/{request_id}` | Server-Sent Events stream of the analysis |
| `GET /health`, `GET /research-state`, `GET /audit/{session_id}` | Health, research state, audit (`api/routes/health.py`, `audit.py`) |

The pipeline runs in `services/live_application.py` (`LiveMedicalRAGService.execute`). Models load lazily on the first request (`_lazy_init_models`).

```
 names / image (+ patient context, + additional instructions)
        │
        ▼
 [uploading] input screening ── injection marker in notes ──► error INPUT_REJECTED
        │   security/sanitizer.py, security_extensions/injection_detector.py
        ▼
 [extracting] (image only) vision model → strict JSON schema → medication_candidates_extracted
        │   llm_backend/openai_vision_backend.py, services/image_validator.py
        │   ──► confirmation_required … POST /confirm (objects) …
        ▼
 [normalizing] RxNorm identity (cache, then RxNav)            → rxnorm
        │   normalization/drug_normalizer.py, entity_cache.py
        ▼
 [retrieving] hybrid BM25 + dense (MiniLM) + graph, RRF       → retrieval
        │   retrieval/hybrid_retrieval.py over LIVE_MEDICAL_CORPUS_V2 (+ approved V2 evidence)
        ▼
 [security_checking] provenance SHA-256 + poisoning detector  → security
        │   security_extensions/poisoning_detector.py
        ▼
 [trust_evaluating] risk tier (R2 default, R3 only from an approved record),
        │   unrelated chunks excluded, trust score vs threshold       → trust
        │   services/live_relationships.py, trust_scoring/trust_scorer.py
        ├── no eligible evidence ──► abstention (served_by: null)
        ▼
 [generating] structured answer from eligible evidence only; provider router with failover
        │   llm_backend/live_provider_router.py, openai_compatible_backend.py, groq_backend.py
        ├── provider failure ──► error LLM_ERROR (served_by: null, requested_model)
        ├── unparseable / schema-invalid output ──► error LLM_OUTPUT_VALIDATION_FAILURE (served_by)
        ▼
 [claim_verifying] each statement vs cited evidence: NLI + canonical relationship identity
        │   verification/claim_verifier_v2.py, verification/canonical_identity.py
        ▼
 [safety_gating] release only if every statement is SUPPORTED → answer (served_by)
        └── otherwise ──► abstention with reasons and the checked evidence (served_by)
```

### 1.1 Stage details

1. **Input screening.** Drug names and patient context are validated. *Additional Instructions* are untrusted data: an instruction aimed at the system, markup or a personal identifier rejects the request (`INPUT_REJECTED`); the log records only the marker name and length.
2. **Image extraction.** `image_validator.py` accepts JPEG, PNG and WebP up to 5 MB. `openai_vision_backend.py` sends the image with the exact JSON schema and `response_format: json_object`. The reply is accepted only as one JSON object, one JSON object in a single code fence, or one narrowly matched bullet format the NVIDIA model was observed to produce; it must contain `candidate_medications` with string `raw_text`. Everything else (prose, embedded or trailing JSON, nested or unclosed fences, malformed or schema-invalid JSON) raises `SCHEMA_ERROR` and the request ends with `VISION_EXTRACTION_ERROR`. The event names `vision_provider` and `vision_model`.
3. **Confirmation.** The user confirms each medication; the confirm body is a list of medication objects (`name`, `status`, `source`, `raw_detected_name`).
4. **Drug identity.** `DrugNormalizer` resolves each name to an RxCUI and generic name (local cache first, then `https://rxnav.nlm.nih.gov/REST`). Each entity reports `rxnorm_source` (`cache`, `rxnorm_exact`, `rxnorm_approx`).
5. **Retrieval.** `HybridRetrievalEngine` fuses BM25, dense vectors (`all-MiniLM-L6-v2`, 384 dimensions; corpus vectors come from the corpus file) and a graph channel with reciprocal rank fusion, over `data/live_medical/LIVE_MEDICAL_CORPUS_V2.json` (14 chunks). Chunks of an approved V2 relationship dataset are added only when an accepted record cites them. The `retrieval` event reports `embedding_mode` (`real`, or `testing_stub` under `TESTING=1`) and `relationship_evidence_chunks`.
6. **Provenance and poisoning.** Each chunk's SHA-256 must equal its provenance `content_hash`; chunks failing that or the poisoning detector are blocked.
7. **Risk tier and eligibility** (section 2.1). `live_risk_tier`: a multi-drug question is R2 ("a multi-drug interaction question with no approved severe relationship record"); R3 only when an approved CONTRAINDICATED or MAJOR record links the pair. A chunk naming none of the requested drugs (whole-word canonical name match) is excluded before scoring (`unrelated_excluded`). A chunk is eligible if its trust score meets the tier threshold (R0 0.30, R1 0.45, R2 0.60, R3 0.75) and its source authority is at least 0.30. Trust factors and weights: `trust_scoring/trust_scorer.py`.
8. **Generation.** The prompt contains only the eligible evidence, numbered `[Source N]`, and treats patient context and notes as data. Automatic mode tries the registered providers in order NVIDIA, Groq, Cloudflare (`LLM_PROVIDER` moves one to the front) with failover; a manually selected model has no failover. Cloudflare gets `max_tokens=4096`. A JSON parse failure logs provider, model, finish reason and length, never the content.
9. **Claim verification.** `ClaimVerifierV2` (NLI model `pritamdeka/PubMedBERT-MNLI-MedNLI`, pinned revision) checks each statement against its cited chunks. A pairwise drug claim also needs a canonical relationship identity, which a chunk carries only from an approved, hash-matched relationship record; predicates must match exactly (a symmetric `BIDIRECTIONAL` record matches either drug order). Model-written research disclaimers are removed from the conclusion rather than verified, when recognised.
10. **Safety gate.** The answer is released only if a verifier ran, there is at least one statement, and every statement is SUPPORTED. Otherwise the result is an abstention listing each claim's support state and identity status.
11. **Browser response.** Evidence items carry `source_link_status` and `source_link_note`; `url` is present only for a link verified for that chunk (`services/live_source_links.py`). Every outcome after generation carries `served_by` (`provider`, `model_id`, `reported_model`, `finish_reason`, `output_length`), read from the provider response.

### 1.2 SSE events

`stage_update`, `medication_candidates_extracted`, `confirmation_required`, `rxnorm`, `retrieval`, `security`, `trust`, `answer`, `abstention`, `error`, `complete`. Stage names: `uploading`, `extracting`, `normalizing`, `retrieving`, `security_checking`, `trust_evaluating`, `generating`, `claim_verifying`, `safety_gating`, `complete`. Error codes include `INPUT_REJECTED`, `VISION_EXTRACTION_ERROR`, `RETRIEVAL_UNAVAILABLE`, `RETRIEVAL_ERROR`, `LLM_ERROR`, `LLM_OUTPUT_VALIDATION_FAILURE`.

## 2. Dual safety gates

### 2.1 Evidence Eligibility Gate (pre-generation)

Applied after retrieval and the provenance/poisoning screen, before anything reaches the LLM. A chunk that names none of the requested drugs is excluded first. Each remaining chunk gets a trust score and is eligible only if the score meets the risk-tier threshold and its source authority is at least 0.30. If no chunk is eligible, the request abstains without calling a model.

#### Source Authority Score

A per-chunk value stored in the corpus (`authority` in `LIVE_MEDICAL_CORPUS_V2.json`): DailyMed labels 0.95, openFDA 0.88, PubMed 0.85–0.90. The live pipeline also uses it for the `evidence_quality` factor. There is no runtime authority-tier lookup on the live path.

#### Freshness Score

A per-chunk value stored in the corpus (`freshness`): DailyMed 0.90, openFDA 0.85, PubMed 0.80 (default 0.8 if absent). The live pipeline does not recompute a time decay at query time.

#### Multi-Factor Trust Score Calculation

`trust_scoring/trust_scorer.py` computes `TrustScore = Σ w_i(R) · S_i / Σ w_i(R)` over nine factors `S_i ∈ [0, 1]`; factors without a value are excluded and the remaining weights renormalised. Weights per risk tier come from `config/trust.yaml` (each row sums to 1.0):

| Factor | R0 | R1 | R2 | R3 | Live-pipeline value |
|---|---|---|---|---|---|
| source_authority | 0.15 | 0.20 | 0.25 | 0.30 | corpus `authority` |
| query_relevance | 0.20 | 0.20 | 0.15 | 0.10 | retrieval score (clamped to [0, 1]) |
| evidence_quality | 0.10 | 0.15 | 0.20 | 0.25 | corpus `authority` |
| freshness | 0.10 | 0.10 | 0.10 | 0.10 | corpus `freshness` |
| consistency | 0.15 | 0.10 | 0.10 | 0.10 | 1 − poisoning score |
| entity_match | 0.10 | 0.10 | 0.10 | 0.10 | 1.0 for a chunk naming a requested drug (others are excluded) |
| population_match | 0.05 | 0.05 | 0.05 | 0.03 | 0.8 default |
| anti_poisoning | 0.10 | 0.05 | 0.03 | 0.01 | 1 − poisoning score |
| anti_injection | 0.05 | 0.05 | 0.02 | 0.01 | 1.0 |

Thresholds: R0 0.30, R1 0.45, R2 0.60, R3 0.75. Live risk tier: R2 for a multi-drug question, R3 only from an approved CONTRAINDICATED or MAJOR relationship record.

### 2.2 Answer Safety Gate (post-generation)

1. The structured answer is split into statements (conclusion, interactions, adverse reactions, warnings, food guidance, patient considerations), with item keys and status labels enforced; an answer that does not match the schema is an `LLM_OUTPUT_VALIDATION_FAILURE`.
2. Each statement's `[Source N]` references must point to retrieved, eligible chunks; any other source makes the statement UNSUPPORTED.
3. `ClaimVerifierV2` checks each statement against its cited chunks with NLI, and a pairwise drug claim must also match the canonical relationship identity of an approved record on the cited chunk.
4. The answer is released only if every statement is SUPPORTED; otherwise the request abstains, listing each claim's support state and the checked evidence.

## 3. Relationship records

`services/live_relationships.py` loads:

- **V1** `data/live_medical/relationships/LIVE_RELATIONSHIP_RECORDS_V1(.json, _MANIFEST.json)`: records citing chunks of the frozen corpus.
- **V2** `LIVE_RELATIONSHIP_RECORDS_V2.json`, `LIVE_RELATIONSHIP_EVIDENCE_V2.json`, `LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json`: records that may cite their own versioned evidence chunks (for example byte-exact label text). No V2 dataset is shipped.

A dataset loads only if its manifest is `APPROVED` with `approved_by` and `approved_at` and the file hashes (LF-normalised) match. Each record must be complete, use a bounded predicate and severity, quote its evidence span verbatim from a chunk with a matching content hash, and name both drugs. Records only ever raise the risk tier. Current state: REL-LIVE-0001 (V1) and REL-LIVE-0002 (V2 candidate, in a run folder) are both pending researcher approval, so no record is loaded.

## 4. Frontend

`frontend/` (Vite, React, TypeScript, Tailwind). `npm run dev` serves on port 5173 and proxies `/api`, `/query`, `/health` and `/research-state` to `http://localhost:8000` (`frontend/vite.config.ts`). `frontend/src/services/api.ts` subscribes to the SSE events above.

## 5. Research harness (separate from the live app)

- `POST /query` (`api/routes/query.py`) and the `medical-rag` CLI (`cli.py`: `query`, `ingest`, `eval`, `report`, `db`, `health`, `research-run`) run the orchestrator in `orchestrator/rag_orchestrator.py` and the evaluation code in `evaluation/`.
- Ablation variants: A vanilla LLM, B dense RAG, C hybrid RAG, D entity-attributed RAG, E trust-scored RAG, F full architecture with dual gates. The published A–F tables come from a simulation profile (`MockVariantPipeline`), not live runs.
- `research-run` writes audit and run artifacts to `--audit-dir` and `--run-dir` (defaults `reports/audit`, `experiments/runs/live-smoke-v1`); tests point these at temporary directories.
### Database Entity-Relationship Schema

Optional PostgreSQL + pgvector database used by the research harness (models in `src/adaptive_trust_medical_rag/database/`, Alembic migrations in `alembic/`): `evidence_sources` → `documents` → `evidence_chunks` (with embeddings), plus `evidence_provenance` (hash log) and `audit_events` (query hashes, risk tier, gate decision and trust scores; no raw queries). The live application does not need it; `/health` reports `database: false` when it is absent.

## 6. Threat Model & Security Mitigations

| Threat | Mitigation in the code |
|---|---|
| Prompt injection in notes or input | Sanitizer and injection detector; notes with injection markers are rejected (`INPUT_REJECTED`); evidence and notes are delimited as data |
| Injection text inside a prescription image | Vision prompt treats image text as literal transcription; extracted names still go through user confirmation and RxNorm |
| Retrieval poisoning or tampering | SHA-256 provenance check per chunk, poisoning detector, unrelated-evidence exclusion |
| Hallucinated or misattributed claims | Claim-level NLI verification, citation index validation, canonical relationship identity from approved records only |
| Misleading source links | Links shown only when verified for the chunk |
| Secrets | Environment variables only; pre-commit regex + gitleaks gate; CI secret-scan hook |
| PHI | Synthetic data only; logs record identifiers and hashes, not raw content |

Full threat model: [THREAT_MODEL.md](THREAT_MODEL.md).

## 7. Research Integrity Policy

From [AGENTS.md](../AGENTS.md) and the code:

- Evaluation splits stay segregated (smoke 20, dev 100, val 200, test 500+); the frozen test set is never used for prompt work, threshold tuning or indexing.
- Frozen artifacts (corpus, prompts, manifests) are never edited; their recorded SHA-256 values are checked by tests and `scripts/audit_frozen_hash_line_endings.py`, with line endings pinned in `.gitattributes` so checkouts reproduce the recorded bytes.
- Relationship records and human labels count only with a named approver and date; nothing is approved on a researcher's behalf.
- Results produced by simulation profiles are labelled as such and are not evidence for the research question.
- Only synthetic data is used; no real patient information.

## 8. Differences from the earlier version of this document

- The earlier diagram placed the eligibility gate before retrieval; the live code retrieves first, then screens provenance, then applies eligibility.
- The live app retrieves in memory from the frozen JSON corpus with 384-dimensional MiniLM vectors; the earlier text described PostgreSQL/pgvector with 768-dimensional vectors as the retrieval store. pgvector belongs to the optional research-harness database.
- The earlier trust formula used four factors with fixed weights (authority, freshness, entity, reputation), authority tiers and a five-year freshness half-life; the code uses nine factors with per-tier weights from `config/trust.yaml`, and on the live path authority and freshness are stored per chunk (section 2.1). The thresholds R0–R3 are unchanged.
- Image extraction, medication confirmation, relationship records, verified-only links and provider tracing did not exist in the earlier version.
