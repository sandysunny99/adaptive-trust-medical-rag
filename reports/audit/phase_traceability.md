# Phase-to-Implementation Traceability Matrix

| Phase | Claimed Capability | Actual Module | Entry Point | Tests | Runtime Verified | Research Purpose | Status |
|-------|--------------------|---------------|-------------|-------|------------------|------------------|--------|
| 1 | Ground Rules & Directives | AGENTS.md, rules/ | Pre-commit hooks | N/A | VERIFIED | Governance & Zero PHI policy | VERIFIED |
| 2 | Input Sanitizer | security/sanitizer.py | sanitize_query() | 18 | VERIFIED | Prompt injection defense | VERIFIED |
| 3 | Drug Entity Normalization | entity_normalization/drug_normalizer.py | normalize_drug_entity() | 22 | VERIFIED | Entity attribution & grounding | VERIFIED |
| 4 | Source Validation & Freshness | source_validation/source_validator.py | validate_source() | 24 | VERIFIED | Provenance & freshness decay | VERIFIED |
| 5 | Adaptive Trust Scoring | trust_scoring/trust_scorer.py | calculate_trust_score() | 28 | VERIFIED | Risk-weighted evidence gating | VERIFIED |
| 6 | Evidence Ingestion Pipeline | ingestion/evidence_ingester.py | ingest_document() | 20 | VERIFIED | SHA-256 validation & quarantine | VERIFIED |
| 7 | Hybrid Retrieval (BM25+Dense+Graph) | retrieval/hybrid_retriever.py | retrieve_evidence() | 26 | VERIFIED | High-recall context retrieval | VERIFIED |
| 8 | Claim Extraction & Verification | claim_verification/claim_verifier.py | verify_claims() | 25 | VERIFIED | Hallucinated claim detection | VERIFIED |
| 9 | Dual Safety Gates Orchestrator | orchestrator/rag_orchestrator.py | execute_rag_pipeline() | 22 | VERIFIED | Controlled abstention gating | VERIFIED |
| 10 | Audit Logging & Provenance | audit/audit_logger.py | log_audit_event() | 18 | VERIFIED | Zero-PHI audit trail | VERIFIED |
| 11 | Risk Classification (R0-R3) | trust_scoring/trust_scorer.py | classify_risk_tier() | 15 | VERIFIED | Adaptive safety thresholds | VERIFIED |
| 12 | System Integration Suite | core/pipeline.py | RAGPipeline | 15 | VERIFIED | End-to-end orchestration | VERIFIED |
| 13 | Evaluation Framework | evaluation/evaluator.py | RAGEvaluator | 47 | VERIFIED | Bootstrap CIs & paired t-tests | VERIFIED |
| 14 | MLflow Experiment Tracker | evaluation/experiment_tracker.py | ExperimentTracker | 35 | VERIFIED | Scientific experiment logging | VERIFIED |
| 15 | Ablation Study Runner | evaluation/ablation_runner.py | AblationRunner | 32 | VERIFIED | 6-variant ablation benchmarking | VERIFIED |
| 16 | Synthetic Dataset Generator | evaluation/dataset_generator.py | generate_dataset() | 46 | VERIFIED | PHI-free dev/val fixtures | VERIFIED |
| 17 | End-to-End Evaluation Pipeline | evaluation/eval_pipeline.py | run_evaluation() | 33 | VERIFIED | Automated markdown reports | VERIFIED |
| 18 | Alembic Database Migrations | database/migration_utils.py | get_migration_chain() | 43 | VERIFIED | PostgreSQL + pgvector schema | VERIFIED |
| 19 | FastAPI HTTP Layer | api/app.py | create_app() | 39 | VERIFIED | Secure REST API endpoints | VERIFIED |
| 20 | CI/CD Pipeline Enhancement | .github/workflows/ci.yml | GitHub Actions | 24 | VERIFIED | 3-job CI & regression gates | VERIFIED |
| 21 | Security Hardening & SAST | .bandit, .semgrep/ | bandit, semgrep | 29 | VERIFIED | SAST & custom security rules | VERIFIED |
| 22 | Statistical Research Report | evaluation/statistical_report.py | generate_statistical_report() | 8 | VERIFIED | Welch t-tests & Cohen d | VERIFIED |
| 23 | Command Line Interface | cli.py | main() | 16 | VERIFIED | Operational CLI tooling | VERIFIED |
| 24 | Publication Documentation | README.md, docs/ARCHITECTURE.md | Documentation | 9 | VERIFIED | Technical specification | VERIFIED |
