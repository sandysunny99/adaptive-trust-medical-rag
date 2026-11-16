# Final Forensic Audit and Verification Report: PR #2 CI Remediation & Model Selector

**Date:** 2026-10-12  
**Repository:** `sandysunny99/adaptive-trust-medical-rag`  
**Pull Request:** [#2](https://github.com/sandysunny99/adaptive-trust-medical-rag/pull/2)  
**Branch:** `fix/ci-remediation-and-model-selector`  
**Target Base:** `main` (commit `e8adf3e`)  
**Verified Final PR Head SHA:** `2cc83ef48ac98c8e99712632daf045e87e2bfd49`  
**Remote CI Run ID:** [38240270244](https://github.com/sandysunny99/adaptive-trust-medical-rag/actions/runs/38240270244)  
**Remote CI Status:** **SUCCESS / ALL REQUIRED JOBS PASSED**  
**Final Audit Status:** **PR READY FOR OWNER MERGE - AUDIT PASSED**  

---

## 1. Executive Summary & Verification Outcome

This audit confirms that all issues identified across the application, CI pipeline, and user-selectable LLM features have been resolved, rigorously verified locally and remotely, and proven without weakening any safety gates, test assertions, or security controls.

Pull Request #2 is currently open with a clean merge state against `main`. **Per strict instructions, PR #2 has NOT been merged.** It awaits the repository owner's merge approval.

### Remote Workflow Run Summary (Run ID: 38240270244)

| Workflow Job | Trigger / Matrix | Status | Conclusion | Notes |
|---|---|---|---|---|
| **Lint, Scan & Unit Tests** | `pull_request` | `completed` | **`success`** | All linters, scans, hooks, and 1,211 unit tests passed |
| **Smoke Ablation Evaluation** | Dependent | `completed` | **`success`** | 20-case smoke evaluation (Variants B + F) completed |
| **Dev Dataset Ablation (main only)** | Branch condition | `completed` | **`skipped`** | Expected: only triggers on direct push to `main` |

---

## 2. Remote Workflow & Job Step Audit (Run 38240270244)

Remote execution on GitHub Actions runner `ubuntu-latest` verified every single step in Job `114780857603` (`Lint, Scan & Unit Tests`):

```
- Step: Set up job                          -> SUCCESS
- Step: Checkout                            -> SUCCESS
- Step: Set up Python 3.12                  -> SUCCESS
- Step: Install uv                          -> SUCCESS (uv 0.12.5)
- Step: Install dependencies                -> SUCCESS
- Step: Install Gitleaks                    -> SUCCESS (v8.21.2)
- Step: Gitleaks secret scan                -> SUCCESS (no leaks detected)
- Step: Bandit SAST scan                    -> SUCCESS (0 medium/high issues)
- Step: Ruff lint                           -> SUCCESS (0 lint violations)
- Step: Unit tests                          -> SUCCESS (1,211 passed, 0 failed, 4 skipped)
- Step: Upload JUnit test report            -> SUCCESS
- Step: Hook - inject_medical_context       -> SUCCESS
- Step: Hook - check_dangerous_cmd allow    -> SUCCESS
- Step: Hook - check_dangerous_cmd deny     -> SUCCESS
- Step: Hook - pre_commit_secret_scan allow -> SUCCESS
- Step: Hook - pre_commit_secret_scan deny  -> SUCCESS
- Step: Verify Alembic migration chain      -> SUCCESS
- Step: API health endpoint smoke test      -> SUCCESS
```

### Enumeration of Skipped Tests in CI (4 Preflight Tests)

The 4 skipped tests in the CI test suite are purely live-cloud credential preflight checks that skip deterministically when external API credentials are absent from the CI environment:

| Test ID | Location | Skip Condition & Reason |
|---|---|---|
| `TestProviderPreflight::test_groq_client_initializes` | `tests/test_provider_connectivity_preflight.py:47` | `pytest.skip("GROQ_API_KEY not set")` — Skipped in CI because external Groq credentials are not provisioned in untrusted/PR runners. |
| `TestProviderPreflight::test_gemini_client_initializes` | `tests/test_provider_connectivity_preflight.py:56` | `pytest.skip("GEMINI_API_KEY not set")` — Skipped in CI because external Gemini credentials are not provisioned in untrusted/PR runners. |
| `TestProviderPreflight::test_hf_client_initializes` | `tests/test_provider_connectivity_preflight.py:65` | `pytest.skip("HF_TOKEN not set")` — Skipped in CI because external HuggingFace credentials are not provisioned in untrusted/PR runners. |
| `TestProviderPreflight::test_cloudflare_client_initializes` | `tests/test_provider_connectivity_preflight.py:82` | `pytest.skip("CLOUDFLARE_API_TOKEN or CLOUDFLARE_ACCOUNT_ID not set")` — Skipped in CI because external Cloudflare credentials are not provisioned in untrusted/PR runners. |

*Note:* No clinical safety, claim verification, retrieval, routing, or security tests were skipped.

Job `114781965340` (`Smoke Ablation Evaluation`):
```
- Step: Run smoke ablation (Variants B + F, 20 cases) -> SUCCESS
- Step: Upload smoke eval report                     -> SUCCESS
```

---

## 3. Forensic Root-Cause Analysis of Preceding Failed Run 38235567758

In preceding run `38235567758` (commit `854ccf9`), the `Unit tests` step failed with 3 errors out of 1,211 tests. 

### A. Failure Manifest
1. `tests/test_model_selector.py::test_server_side_validation_matrix`
2. `tests/test_model_selector.py::test_analyze_request_server_validation_rejection`
3. `tests/test_model_selector.py::test_prescription_endpoint_strict_model_validation`

### B. Root Cause
In commit `854ccf9`, we hardened server-side model validation:
- When an active router exists on `app.state.llm_backend`, availability strictly requires that the selected provider is genuinely registered in `router.providers` and that the adapter's configured model ID matches the registry.
- When `tests/test_model_selector.py` was executed in isolation, `app.state.llm_backend` was `None` (no API keys configured in test environment), so validation operated in standard fallback mode.
- However, when the full test suite ran alphabetically, `tests/e2e/test_v6_c8_multimodal_claim_citation_safety.py` and `tests/e2e/test_v6_c9_multimodal_full_e2e_audit.py` executed *before* `tests/test_model_selector.py`.
- Both E2E tests populated `app.state.llm_backend = MockRouter()` where `MockRouter.providers = {"mock": MockLLMBackend()}`.
- Neither test restored `app.state.llm_backend` in fixture teardown.
- Consequently, when `test_model_selector.py` ran, it inherited the mutated global `MockRouter` containing only provider `"mock"`. When `test_server_side_validation_matrix` and the analyze endpoints requested valid production models (e.g. `openai/gpt-oss-120b` on `groq` or `nemotron` on `nvidia`), the hardened validator correctly observed that neither `groq` nor `nvidia` was registered in the active router, rejecting the request with HTTP 400.

### C. Remediation in Commit 2cc83ef
1. **Fixture Teardown Restoration:** Added complete save-and-restore teardown logic to `base_mocks` in `tests/e2e/test_v6_c8_multimodal_claim_citation_safety.py` and `setup_c9_mocks` in `tests/e2e/test_v6_c9_multimodal_full_e2e_audit.py` for `llm_backend`, `vision_backend`, `retrieval_engine`, and `claim_verifier`.
2. **Model Selector Test Isolation:** Added an `autouse=True` fixture `clean_app_state` in `tests/test_model_selector.py` to ensure every test in that module begins with a pristine `app.state` and restores previous state on exit.
3. **Outcome:** 100% of tests passed both locally (`1,211 passed in 130.76s`) and remotely on GitHub Actions (Run ID `38240270244`).

---

## 4. Four Core Application-Correctness Audit Invariants

### Invariant 1: Frontend Catalog Error Contract Harmonization
- **File:** `frontend/src/services/api.ts`
- **Issue:** `fetchModelCatalog()` previously caught network/HTTP errors and silently returned `[]`, preventing the `.catch()` handler in `WorkspacePage.tsx` from displaying the error banner.
- **Fix:** Removed error-swallowing try/catch block. `fetchModelCatalog()` now propagates an `Error("Failed to fetch model catalog: HTTP ...")`.
- **UI & Accessibility:** Added `aria-label="Answer-generation model"` to the `<select>` element in `WorkspacePage.tsx`.
- **Test Coverage:** Added `frontend/src/pages/WorkspacePage.test.tsx` verifying:
  - Warning `"Could not load remote model catalog. Defaulting to automatic routing."` renders on fetch rejection.
  - Disabled `<option>` elements for unconfigured/unavailable models.
  - Vitest results: 12 tests passed across 2 suites. Vite production build passed.

### Invariant 2: Provider Availability Invariant in Model Registry
- **File:** `src/adaptive_trust_medical_rag/llm_backend/model_registry.py`
- **Issue:** Previously, `get_available_models()` and `validate_llm_selection()` fell back to checking raw environment variables even when an active `LiveProviderRouter` was running without that provider registered.
- **Fix:** When `has_active_router` is True (`router` exists and has `providers`), availability strictly requires:
  1. `m.provider in registered_providers`.
  2. If the registered adapter defines `model_name`, `adapter.model_name == m.id`.
- **Behavioral Proof:** Tested via `test_provider_availability_requires_live_router_registration`:
  - Registered Groq model -> available.
  - Unregistered NVIDIA model with `NVIDIA_API_KEY` present in environment -> rejected with HTTP 400 (`not configured or available on the server`).
  - Model mismatch -> rejected with explanatory error.

### Invariant 3: Decoupled Vision-Language Model Initialization
- **File:** `src/adaptive_trust_medical_rag/api/app.py`
- **Issue:** `app.state.vision_backend` was previously nested inside the Cloudflare credential block (`if CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID:`), causing NVIDIA Vision initialization to be skipped if Cloudflare was unconfigured.
- **Fix:** Un-nested `vision_backend`. It now initializes independently based strictly on `nvidia_api_key`.
- **Behavioral Proof:** Tested via `test_vision_backend_initialization_decoupling` across all permutations:
  - NVIDIA key present, Cloudflare keys absent -> `vision_backend` initializes.
  - Cloudflare keys present, NVIDIA key absent -> Cloudflare router registers, `vision_backend` is `None`.

### Invariant 4: Behavioral Vision-Language Model Pipeline Isolation
- **File:** `tests/test_model_selector.py`
- **Issue:** Prior isolation tests only inspected `ImageValidator` metadata rather than proving independent execution of the Vision-Language Model adapter.
- **Fix:** Created `test_behavioral_vision_language_model_isolation` using a controlled `VisionProviderAdapter` double (`ControlledVisionModelDouble`).
- **Behavioral Proof:**
  - Proves prescription image upload triggers `extract_medications` on the Vision-Language Model adapter.
  - Proves candidate medications (`metformin`, `lisinopril`) are extracted with `source="VISION"`.
  - Proves the pipeline pauses at `confirmation_required` awaiting user verification.
  - Proves changing the user-selected text LLM (`openai/gpt-oss-120b` vs `nvidia/nemotron-3-super-120b-a12b`) does NOT invoke the text LLM during image extraction (`call_count == 0`), leaving the vision extraction completely independent.
  - Provenance records explicitly capture `vision_provider` and `vision_model`.

---

## 5. Mocked Claim Verification vs. Real Model Execution Disclosure

- **CI Mode:** All unit and integration tests run with `TESTING=1`.
- **ClaimVerifierV2 Behavior in CI:** In `TESTING=1` mode, `ClaimVerifierV2` uses a deterministic rule-based mock classifier for NLI orchestration testing rather than downloading real 440MB Hugging Face transformer weights (`pritamdeka/PubMedBERT-MNLI-MedNLI`) or running PyTorch CUDA/CPU inferences on ephemeral runners.
- **Embedding Model in CI:** `HybridRetrievalEngine` uses a 384-dimensional dense mock transformer during CI.
- **Live Variant Mode:** Full research evaluations (e.g. `RealVariantRunner` for Track A/B variants) load real models when running on GPU-equipped evaluation nodes with valid API keys.
- **Integrity Statement:** This audit explicitly discloses that CI green status confirms deterministic pipeline orchestration, gate logic, and contract enforcement, and does NOT imply that real Hugging Face model weights were executed during CI.

---

## 6. Changed Files & Git Commit Accounting

### Commit History on Branch `fix/ci-remediation-and-model-selector`
- `c62c1ba`: `feat: remediate CI test failures and implement user-selectable LLM models`
- `135f519`: `fix: enforce strict model validation, align model labels, and strengthen component isolation tests`
- `854ccf9`: `fix: decouple vision initialization, enforce live router availability, and fix catalog error handling`
- `2cc83ef`: `test: isolate app.state between e2e fixtures and model selector tests` (HEAD)

### Full Diffstat vs. Base `main` (`e8adf3e..2cc83ef`)
```
 .github/workflows/ci.yml                           |   4 +-
 frontend/src/components/Layout.tsx                |   8 +-
 .../MedicationConfirmationPanel.test.tsx           | 216 +++++++++++++
 .../components/MedicationConfirmationPanel.tsx     | 108 ++++++-
 frontend/src/pages/WorkspacePage.test.tsx          |  81 +++++
 frontend/src/pages/WorkspacePage.tsx               | 122 ++++++-
 frontend/src/services/api.ts                       |  38 ++-
 frontend/src/types/index.ts                        |  16 +
 pyproject.toml                                     |   5 -
 src/adaptive_trust_medical_rag/api/app.py          |  13 +-
 .../adaptive_trust_medical_rag/api/routes/admin.py |   1 +
 .../api/routes/analyze.py                          |  28 +-
 .../adaptive_trust_medical_rag/api/schemas.py      |  25 ++
 .../llm_backend/live_provider_router.py            |  36 ++-
 .../llm_backend/model_registry.py                  | 197 ++++++++++++
 .../services/live_application.py                   | 104 ++++--
 .../verification/claim_verifier_v2.py              |  14 +-
 .../test_v6_c8_multimodal_claim_citation_safety.py |  10 +
 tests/e2e/test_v6_c9_multimodal_full_e2e_audit.py  |  10 +
 tests/test_model_selector.py                       | 582 +++++++++++++++++++++++++++++++++
 20 files changed, 1564 insertions(+), 54 deletions(-)
```

---

## 7. Security & Compliance Checklist

- [x] **Zero PHI:** Only synthetic drug names and mock patient fixtures used.
- [x] **Zero Secrets:** `gitleaks git --verbose --redact` scanned all 129 commits: 0 leaks found. Pre-commit hook verified.
- [x] **Static Analysis:** Bandit passed with 0 medium/high severity issues.
- [x] **Linter:** Ruff passed with 0 issues across all directories.
- [x] **Security Hooks:** All CI security and medical context hooks passed in CI.
- [x] **Safety Gates:** Evidence eligibility gate and claim verification safety gates are fully active and enforced.
- [x] **Frozen Artifacts:** `experiments/` and `reports/audit/` remain intact and uncorrupted.

---

## 8. Runner Deprecation & Runtime Maintenance Note

- **Ubuntu OS Label Lifecycle (October 12, 2026):** GitHub Actions `ubuntu-latest` is currently running Ubuntu 24.04 (`noble`) under Python 3.12.10. GitHub's runner-image roadmap has scheduled the `ubuntu-latest` label transition to Ubuntu 26.04 in November 2026.
- **Node.js Runtime Maintenance (October 12, 2026):** GitHub Actions runners no longer support the Node.js 20 runtime as of September 23, 2026. JavaScript actions must use Node.js 24-compatible releases. The audited workflow completed successfully; therefore, no CI failure attributable to this transition was observed in the verified run. Review future runtime annotations and update action versions when required.
- These notifications represent upcoming host environment lifecycle events and do not affect current build correctness or test execution.

---

## 9. Final Recommendation

**Status:** `PR READY FOR OWNER MERGE - AUDIT PASSED`

PR #2 (`fix/ci-remediation-and-model-selector`) satisfies all functional, architectural, and security requirements. Remote CI run `38240270244` on commit `2cc83ef` is fully green. The branch is clean, conflict-free, and ready to be merged by the repository owner.
