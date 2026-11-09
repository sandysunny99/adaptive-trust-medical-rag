# CI Check Forensic Report

## Job Execution Breakdown

**Pipeline:** `.github/workflows/ci.yml`
**Trigger:** Push to `main`

### Job 1: `lint-and-test`
**Status:** **FAILED**
**Stages:**
- `uv sync --frozen`: PASSED
- `gitleaks detect`: PASSED
- `bandit`: PASSED
- `ruff check`: FAILED (Syntax errors, formatting warnings)
- `pytest tests/`: FAILED (Fatal collection error)
**Forensic Findings:**
The `pytest` runner failed immediately during test collection with `AttributeError` while trying to patch `adaptive_trust_medical_rag.api.app.HybridRetrievalEngine`. Because this error occurred at module import time, zero tests were executed.

### Job 2: `smoke-eval`
**Status:** **SKIPPED**
**Forensic Findings:**
Defined in the workflow with `needs: lint-and-test`. Because Job 1 returned a non-zero exit code, GitHub Actions automatically skipped this job.

### Job 3: `dev-eval`
**Status:** **SKIPPED**
**Forensic Findings:**
Defined in the workflow with `needs: smoke-eval`. Skipped due to cascading failure.

## Remediation Applied
- Fixed the mock path in the `test_v6` suite from `adaptive_trust_medical_rag.api.app.HybridRetrievalEngine` to `adaptive_trust_medical_rag.retrieval.hybrid_retrieval.HybridRetrievalEngine`.
- Disabled the `RateLimitMiddleware` during `pytest` execution to prevent 429 Too Many Requests failures.
- Fixed `UnboundLocalError` inside `live_application.py` caused by a misplaced local `import hashlib`.
