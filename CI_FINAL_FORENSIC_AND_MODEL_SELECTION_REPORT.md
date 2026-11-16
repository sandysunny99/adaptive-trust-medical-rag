# CI Remediation and User-Selectable LLM Model Feature: Forensic Verification Report

**Repository:** `sandysunny99/adaptive-trust-medical-rag`  
**Feature Branch:** `fix/ci-remediation-and-model-selector`  
**Base Branch:** `main`  
**Verified Feature Commit:** `135f51985f0074d5d3fca4aa7224599d7c25e0d6`  
**Pull Request:** [#2 — fix: restore CI stability and add user-selectable LLM models](https://github.com/sandysunny99/adaptive-trust-medical-rag/pull/2)  
**Remote CI Run ID:** `38221765509`  
**Remote CI Run URL:** [GitHub Actions Run 38221765509](https://github.com/sandysunny99/adaptive-trust-medical-rag/actions/runs/38221765509)  
**Remote CI Status:** `completed`  
**Remote CI Conclusion:** `success` :white_check_mark:  

---

## 1. Executive Summary

This forensic report documents the complete remediation of previous CI pipeline failures and the audited implementation of user-selectable LLM models in the Adaptive Trust-Aware Medical RAG platform.

All four investigative areas requested have been resolved, verified locally, and independently validated through remote GitHub Actions CI:
1. **Model Registry Label Alignment:** Canonical Groq model ID `openai/gpt-oss-120b` was aligned to display name `"Groq GPT-OSS 120B"` with factual biomedical capabilities description.
2. **Strict Server-Side Validation:** Server-side validation via `validate_llm_selection()` rejects unsupported model IDs and client-supplied provider mismatches with HTTP 400. All client substring guessing in routing was eliminated.
3. **Prescription Upload Error Handling:** Prescription upload endpoint `POST /api/v1/analyze/prescription` strictly parses `llm_selection` JSON and rejects invalid inputs with HTTP 400 without silent fallback to Automatic mode.
4. **Behavioral Component Segregation Proof:** Added behavioral integration tests in `tests/test_model_selector.py` proving strict 4-way component segregation:
   - **User LLM:** Final analysis generation ONLY.
   - **PubMedBERT-MNLI-MedNLI:** Claim verification ONLY.
   - **`all-MiniLM-L6-v2` (384-d):** Dense retrieval embeddings ONLY.
   - **Vision Provider:** Prescription OCR extraction ONLY.

---

## 2. Remote GitHub Actions CI Verification

The remote CI workflow was triggered upon creating Pull Request [#2](https://github.com/sandysunny99/adaptive-trust-medical-rag/pull/2) targeting `main`.

### Workflow Summary: Run `38221765509`

| Job | Status | Conclusion | Key Completed Steps |
|---|---|---|---|
| **Lint, Scan & Unit Tests** | `completed` | `success` | Gitleaks scan, Bandit SAST scan, Ruff lint, Python unit tests (1,208 passed), 7 CI security/context hooks, Alembic migration verification, API health smoke test |
| **Smoke Ablation Evaluation** | `completed` | `success` | Smoke ablation execution (Variants B + F, 20 cases), eval report upload |
| **Dev Dataset Ablation (main only)** | `completed` | `skipped` | Expected skipped behavior on PR branch (runs only on push to `main`) |

**Overall Conclusion:** **GREEN (`success`)** :white_check_mark:

---

## 3. Four Core Audit Findings & Implementations

### Finding 1: Groq Model ID and Name Mismatch
* **Root Cause:** In `model_registry.py`, model ID `openai/gpt-oss-120b` was erroneously labeled `"Groq Llama-3.3 70B Versatile"`.
* **Resolution:** Corrected name to `"Groq GPT-OSS 120B"`, set description to `"Open-weights model inference hosted on Groq."`, and specified required environment variable `GROQ_API_KEY`.
* **Credential Requirements:** Updated Cloudflare definition (`@cf/meta/llama-3.3-70b-instruct-fp8-fast`) to require both `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID`. Set `is_test_only=True` on `mock-llm`.

### Finding 2: Server-Side Validation of Model Selection
* **Root Cause:** Client-provided `provider` could override model mappings or guess provider identity via substring matching (`"groq" in model_id.lower()`).
* **Resolution:** 
  - Implemented `validate_llm_selection(selection, app_state)` in `model_registry.py`.
  - Enforced in `api/routes/analyze.py`: raises `HTTPException(status_code=400, detail=...)` for unknown model IDs or mismatched provider parameters.
  - In `live_application.py`, replaced all substring guessing with deterministic lookup via `get_model_definition(model_id)`.
  - In `LiveProviderRouter`, manual requests route directly with `provider_name` and do NOT fail over to secondary providers on transport errors.

### Finding 3: Prescription Upload Validation Hardening
* **Root Cause:** In `POST /api/v1/analyze/prescription`, errors decoding `llm_selection` were logged as warnings and ignored, silently defaulting to Automatic mode.
* **Resolution:** 
  - Added strict JSON decoding and schema validation.
  - Invalid JSON raises `HTTPException(status_code=400, detail="Invalid llm_selection JSON")`.
  - Validation failures through `validate_llm_selection` raise `HTTPException(status_code=400, detail=err)`.

### Finding 4: Behavioral Component Segregation Tests
* **Root Cause:** Previous test in `test_model_selector.py` only verified class imports without checking execution isolation.
* **Resolution:** Replaced with behavioral tests verifying:
  - **Component 1 (Retrieval):** `HybridRetrievalEngine` operates over dense vectors of dimension 384 (`all-MiniLM-L6-v2`), independent of the generation model.
  - **Component 2 (Verification):** `ClaimVerifierV2` verifies claims against evidence using `PubMedBERT-MNLI-MedNLI` (`model_id="pritamdeka/PubMedBERT-MNLI-MedNLI"`).
  - **Component 3 (Vision):** `ImageValidator` and vision adapter handle image preprocessing and OCR metadata without invoking generation models.
  - **Component 4 (Router & Failover):** `LiveProviderRouter` executes direct routing for manual selection without failover, while automatic mode performs fallback on transport failure.

---

## 4. Local Validation Verification Summary

| Validation Check | Command | Result |
|---|---|---|
| **Python Unit & Integration Tests** | `uv run pytest tests/ -v` | **1,208 passed**, 0 failed (3402.48s) |
| **Model Selector Test Suite** | `uv run pytest tests/test_model_selector.py -v` | **7 passed**, 0 failed |
| **Code Linting** | `uv run ruff check src/ tests/ .agents/scripts/` | **0 errors**, all checks passed |
| **AST Security SAST** | `uv run python .agents/scripts/ci/run_bandit.py` | **0 medium/high severity issues** |
| **Secret Scanning** | `gitleaks git --verbose --redact` | **128 commits scanned, 0 leaks** |
| **CI Security & Context Hooks** | 7 check scripts in `.agents/scripts/ci/` | **All 7 checks PASSED** |
| **Frontend Unit Tests** | `npm test` (`vitest run` in `frontend/`) | **10 passed**, 0 failed |
| **Frontend Production Build** | `npm run build` (`tsc -b && vite build`) | **0 errors**, built clean in 1.60s |

---

## 5. Frontend UI Implementation Details

1. **Workspace Model Selector Dropdown (`WorkspacePage.tsx`):**
   - Populated dynamically from `GET /api/v1/llm/models`.
   - Defaults to `Automatic selection (recommended)`.
   - Displays configured vs unconfigured models (`— Not configured` disabled state).
   - Disabled while analysis is processing (`isProcessing`) or while fetching catalog (`isLoadingModels`).
   - Graceful fallback with user warning if catalog fetch fails.
2. **Analysis Hook & API Client Integration:**
   - Selected model is included in `llm_selection` payload sent to `/api/v1/analyze` and `/api/v1/analyze/prescription`.
   - SSE streaming receives analysis events and records used model provenance.

---

## 6. Merge Recommendation

> [!IMPORTANT]
> **Merge Recommendation for Repository Owner:** **READY TO MERGE**
> 
> - **PR Link:** https://github.com/sandysunny99/adaptive-trust-medical-rag/pull/2
> - **Source Branch:** `fix/ci-remediation-and-model-selector`
> - **Target Branch:** `main`
> - **Remote CI:** Verified Green on GitHub Actions Run `38221765509`.
> - **Policy Compliance:** In accordance with instructions, this PR has NOT been merged automatically and awaits explicit owner review and approval.
