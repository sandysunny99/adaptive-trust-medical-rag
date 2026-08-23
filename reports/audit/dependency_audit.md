# Project Dependency & Environment Audit

All package dependencies are managed using `uv` and tracked in `pyproject.toml` and `uv.lock`.

| Package | Version Requirement | Category | Primary Purpose | Used By | Security Audit |
|---------|---------------------|----------|-----------------|---------|----------------|
| `fastapi` | `>=0.141.1` | Core | HTTP Web Framework | `api/app.py` | Clean (No vulnerabilities) |
| `pydantic` | `>=2.13.4` | Core | Data Validation & Schemas | `api/schemas.py`, `core/config.py` | Clean |
| `pydantic-settings` | `>=2.15.0` | Core | Environment Variable Config | `core/config.py` | Clean |
| `python-dotenv` | `>=1.2.3` | Core | Local .env Loading | `core/config.py` | Clean |
| `sqlalchemy[asyncio]` | `>=2.0.52` | Core | Async ORM & Database Access | `database/models.py` | Clean |
| `alembic` | `>=1.19.1` | Core | Schema Migrations | `database/migration_utils.py` | Clean |
| `asyncpg` | `>=0.31.0` | Core | Async PostgreSQL Driver | `database/` | Clean |
| `pgvector` | `>=0.5.0` | Core | Vector Similarity Search | `retrieval/hybrid_retriever.py` | Clean |
| `pyyaml` | `>=6.0.3` | Core | YAML Config & Test Parsing | `tests/test_ci_pipeline.py` | Clean |
| `bandit` | `>=1.9.4` | Dev | Static Security Analysis (SAST) | Security Gates / CI | Clean |
| `pytest` | `>=9.1.1` | Dev | Unit & Integration Test Runner | Test Suite | Clean |
| `pytest-asyncio` | `>=1.4.0` | Dev | Async Test Execution | Test Suite | Clean |
| `ruff` | `>=0.16.3` | Dev | Fast Python Linter & Formatter | Pre-commit / CI | Clean |

**Dependency Policy:** Zero unpinned dependencies allowed. All installs must go through `uv add`.
