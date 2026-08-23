# Complete Codebase Module Inventory

| Module | Purpose | Dependencies | Used By | Test Count | Integration Coverage | Reuse Candidate | Risk |
|--------|---------|--------------|---------|------------|----------------------|-----------------|------|
| `core/config.py` | Environment settings & configuration | `pydantic-settings` | All modules | 10 | High | No (Domain-specific) | Low |
| `security/sanitizer.py` | Regex & semantic prompt injection defense | `re` | Pipeline, API, CLI | 18 | High | Yes (Security reusable) | Low |
| `entity_normalization/drug_normalizer.py` | RxNorm RxCUI & scispaCy normalization | `re`, `json` | Retrieval, Trust Scorer | 22 | High | Yes (Medical entity) | Low |
| `source_validation/source_validator.py` | Source authority & freshness decay | `math`, `datetime` | Trust Scorer, Ingestion | 24 | High | No | Low |
| `trust_scoring/trust_scorer.py` | Multi-factor trust score calculation | `source_validator`, `drug_normalizer` | Pre-Gen Eligibility Gate | 28 | High | No | Low |
| `ingestion/evidence_ingester.py` | SHA-256 ingestion & quarantine check | `hashlib` | Ingestion, API | 20 | High | Yes (Ingestion pattern) | Low |
| `retrieval/hybrid_retriever.py` | BM25 + Dense Vector + Graph RRF | `pgvector`, `math` | RAG Pipeline | 26 | High | No | Low |
| `claim_verification/claim_verifier.py` | Claim extraction & citation check | `re` | Post-Gen Safety Gate | 25 | High | Yes (Verification logic) | Low |
| `orchestrator/rag_orchestrator.py` | Dual safety gate execution & fallback | All core modules | API, CLI, Pipeline | 22 | High | No | Low |
| `audit/audit_logger.py` | Zero-PHI SHA-256 query audit log | `hashlib`, `json` | Pipeline, API | 18 | High | Yes (Telemetry) | Low |
| `database/migration_utils.py` | Alembic migration chain introspection | `alembic` | API, CLI, Tests | 43 | High | Yes (Database utils) | Low |
| `api/app.py` | FastAPI application factory | `fastapi`, `pydantic` | HTTP Service | 39 | High | Yes (API template) | Low |
| `evaluation/evaluator.py` | RAG metrics, bootstrap CIs, t-tests | `math`, `statistics` | Evaluation pipeline | 47 | High | Yes (Metrics engine) | Low |
| `evaluation/experiment_tracker.py` | Experiment hashing & JSONL/MLflow log | `hashlib`, `json` | Ablation runner | 35 | High | Yes (Experiment log) | Low |
| `evaluation/ablation_runner.py` | 6-variant ablation study runner | `evaluator`, `experiment_tracker` | Eval pipeline | 32 | High | No | Low |
| `evaluation/dataset_generator.py` | Synthetic R0-R3 dataset generator | `json`, `random` | Eval pipeline, CLI | 46 | High | No | Low |
| `evaluation/eval_pipeline.py` | End-to-end evaluation runner | `ablation_runner`, `evaluator` | CLI, CI/CD | 33 | High | No | Low |
| `evaluation/statistical_report.py` | Statistical report generator | `evaluator`, `math` | CLI, Evaluation | 8 | High | No | Low |
| `cli.py` | Command Line Interface (`medical-rag`) | `argparse`, `json` | Operational CLI | 16 | High | No | Low |
