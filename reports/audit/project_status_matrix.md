# Project Status Matrix

**Audit Date:** 2026-08-30  
**Commit:** 4a704f5  

| Area | Status | Evidence | Blocking Paper? |
|---|---|---|---|
| Core RAG Pipeline | 🟡 YELLOW | Implemented + 645 tests; no real LLM backend | YES |
| Input Sanitization | 🟢 GREEN | 25 injection patterns, unit tested | NO |
| Drug Normalization | 🟢 GREEN | Live RxNorm API, unit tested | NO |
| Risk Classification | 🟢 GREEN | R0-R3 logic, config-driven, unit tested | NO |
| BM25 Retrieval | 🟢 GREEN | Pure-Python Okapi BM25, unit tested | NO |
| Dense Retrieval | 🔴 RED | 7-word toy vocabulary (SimpleEmbeddingModel) - not semantic | YES |
| Graph Retrieval | 🟡 YELLOW | Hardcoded adjacency list - functional but prototype | NO |
| RRF Fusion | 🟢 GREEN | k=60, correct implementation | NO |
| Trust Scoring | 🟢 GREEN | Config-driven 9-factor weighted heuristic, unit tested | NO |
| Evidence Eligibility Gate | 🟢 GREEN | Threshold-based pre-generation gate, unit tested | NO |
| LLM Integration | 🔴 RED | LiveModelAdapter generates template string - NOT a real LLM | YES |
| Claim Verifier | 🟡 YELLOW | Rule-based lexical overlap - NOT NLI-based; functional but limited | NO |
| Answer Safety Gate | 🟡 YELLOW | Rule-based; limited semantic coverage | NO |
| Evidence Ingestion | 🟢 GREEN | SHA-256 hashing, provenance, unit tested | NO |
| Source Validation | 🟢 GREEN | Authority tiering, freshness decay, unit tested | NO |
| P0 APIs (PubMed/EuropePMC/RxNorm/openFDA) | 🟢 GREEN | Live calls verified, snapshot created | NO |
| Evidence Corpus | 🔴 RED | 4-18 documents total - insufficient for publication | YES |
| Forensic Verifier | 🟢 GREEN | Genuinely independent (stdlib only), unit tested | NO |
| F0F1 Integrity Auditor | 🟢 GREEN | PASS verdict verified | NO |
| F0/F1 Retrieval Experiment | 🟡 YELLOW | Real retrieval + trust; mock LLM; valid for retrieval claims only | YES (faithfulness invalid) |
| Ablation A-F | 🔴 RED | Mock LLM; Variant B=C confound; no valid results | YES |
| 20-case Smoke Run | 🔴 RED | execution_type: simulation confirmed in summary.json | YES |
| Dataset (dev/val) | 🟡 YELLOW | Synthetic generated; no real clinical queries | YES |
| Frozen Test Set | 🔴 RED | Not yet created or frozen | YES |
| Literature Review | 🔴 RED | 0 verifiable citations in current review | YES |
| Statistical Analysis | 🟡 YELLOW | Wilcoxon/CI correct but no multiple-testing correction | YES |
| Web API | 🟡 YELLOW | FastAPI routes implemented; no live DB connection | NO |
| Frontend UI | 🔴 RED | Not implemented | NO (future work) |
| CI/CD | 🟢 GREEN | Ruff + Bandit + Gitleaks + Pytest + Trivy all automated | NO |
| Database / Alembic | 🟡 YELLOW | Models defined, migrations exist; no live DB in experiments | NO |
| Security Controls | 🟡 YELLOW | Rule-based injection defense implemented; adversarial eval missing | YES |
| SLM Variant G | 🔴 RED | Not implemented (correctly deferred) | NO |

## Legend
- 🟢 GREEN: Complete and verified; no blocking issues
- 🟡 YELLOW: Implemented but requires validation or has known limitations
- 🔴 RED: Missing, invalid, or blocking

## Summary Counts
- GREEN: 13 components
- YELLOW: 10 components  
- RED: 10 components
