# Repository map

How the repository is laid out and which parts are live code, research tooling, data or history. The live
application's data flow is in [ARCHITECTURE.md](ARCHITECTURE.md); setup is in [CONFIGURATION.md](CONFIGURATION.md).

## Work tree

```text
adaptive-trust-medical-rag/
├── README.md, AGENTS.md, CLAUDE.md, SECURITY.md   entry documents and contributor rules
├── pyproject.toml, uv.lock, .python-version        Python project (managed with uv only)
├── alembic.ini, alembic/                           database migrations (research harness)
├── docker-compose.yml, infra/postgres/             local PostgreSQL + pgvector
├── config/trust.yaml                               trust-score weights and risk-tier thresholds
├── src/adaptive_trust_medical_rag/                 the Python package (see below)
├── frontend/                                       Vite + React user interface (proxies /api to the backend)
├── tests/                                          pytest suite (the only test path CI runs)
│   ├── e2e/                                        end-to-end tests of the live pipeline
│   ├── security/                                   security-control tests
│   ├── providers/, annotation/, api/, fixtures/
├── data/
│   ├── live_medical/                               frozen live corpus, manifests, relationship records
│   ├── evidence/                                   evidence manifests
│   └── drug_entity_cache.json                      local RxNorm entity cache
├── scripts/                                        research and data-preparation tools (run by hand)
├── experiments/                                    frozen research datasets, runs, prompts and harnesses
├── track_a_annotation/                             Track A relevance-annotation workspace and exports
├── reports/                                        current audit register and validation reports
│   ├── audit/blocked_issue_register.md             authoritative list of open items
│   └── live_validation/                            live-application validation runs
├── paper/                                          IEEE paper (main.tex, main.pdf)
├── docs/                                           current documentation (this folder)
│   ├── architecture/, security/, integrations/     design notes for extensions
│   └── archive/                                    historical reports, kept for provenance (see its README)
├── .github/workflows/                              CI (lint, Bandit, gitleaks, pytest) and Trivy
├── .githooks/                                      local pre-commit secret scan
├── .agents/, .claude/                              agent rules, skills and safety hooks
└── .env.example                                    configuration template (copy to .env; never commit .env)
```

## The Python package (`src/adaptive_trust_medical_rag/`)

| Module | Role |
|---|---|
| `api/` | FastAPI app, middleware, routes and the live analysis endpoints (Server-Sent Events) |
| `services/` | `live_application.py` (the live pipeline, from medication names to a released answer or an abstention), relationship records, verified source links, image validation |
| `normalization/` | drug-name normalisation to RxNorm (RxCUI) with a local entity cache |
| `retrieval/` | hybrid retrieval (BM25 and dense embeddings), Cognee graph adapter, reranker |
| `trust_scoring/`, `source_validation/` | multi-factor trust score with risk-tier thresholds; source authority and freshness |
| `security/` | input and document sanitiser, security context, controlled tool execution |
| `security_extensions/` | injection and poisoning detectors, integrity validation, relationship grounding |
| `verification/` | NLI claim verifiers (v1, v2) and canonical relationship identity |
| `llm_backend/` | provider adapters (Groq, Cloudflare, Gemini, Hugging Face, mock), live provider router, model registry |
| `llm_routing/` | routing with retry, health checks and a circuit breaker |
| `orchestrator/`, `core/`, `common/` | RAG orchestrator, configuration, shared result types |
| `evidence_sources/` | PubMed, Europe PMC, openFDA and RxNorm adapters, query router, deduplication |
| `ingestion/`, `database/` | evidence ingestion with SHA-256 provenance; ORM models and sessions |
| `evaluation/`, `research_harness/`, `security_evaluation/` | evaluator, ablation runner, experiment tracking; gate and approval tooling; security-evaluation schemas |
| `annotation/`, `context_engine/`, `research_memory/`, `skills/` | annotation engine; session context and retrieval traces; research memory; skill definitions |
| `prompts/` | frozen live-application prompt and its hash |
| `cli.py` | the `medical-rag` command line |

## What is live code and what is history

- **Live code:** `src/`, `frontend/`, `config/`, `data/live_medical/`, `alembic/`.
- **Checked by CI:** `tests/` (pytest), `src/`, `tests/` and `.agents/scripts/` (ruff), Bandit, gitleaks.
- **Research tooling:** `scripts/` and the Python files in `experiments/` are run by hand to build or audit datasets.
  They are not imported by the package.
- **Frozen research data:** `experiments/`, `track_a_annotation/`. Do not edit; results and hashes depend on them.
- **History:** `docs/archive/` holds the reports that used to sit at the repository root. A few research scripts
  read or write files there (paths updated when the files moved).
