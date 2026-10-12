# CI Remediation and User-Selectable LLM Model Remediation Plan

## Phase 0: Baseline & Repository Inventory

- **Repository**: `sandysunny99/adaptive-trust-medical-rag`
- **Active Working Branch**: `fix/ci-remediation-and-model-selector`
- **Baseline Git SHA**: `1f639dbccdd8dc4e0ef683f2dd4f7dfd5b91085f`
- **Remote Origin**: `https://github.com/sandysunny99/adaptive-trust-medical-rag.git`
- **Working Tree State**:
  - Uncommitted changes from previous debug sessions preserved in Git stash `previous-debug-session-changes-2026-10-12`.
  - Untracked temporary files identified (to be excluded/cleaned up prior to final feature commits).
  - Clean working branch `fix/ci-remediation-and-model-selector` created without rewriting git history.

---

## Phase 1 & 2: Failure Inventory & Root Cause Analysis

From GitHub Actions run [37771603470](https://github.com/sandysunny99/adaptive-trust-medical-rag/actions/runs/37771603470) (commit `1f639db`) and forensic code analysis:

### 1. Workspace Configuration Failure (`uv` runner crash)
- **Failure**: Any invocation of `uv` in CI or locally fails if `cognee_service` is listed as a workspace member because `cognee_service` has no `pyproject.toml`.
- **Root Cause**: `pyproject.toml` contains `[tool.uv.workspace] members = ["cognee_service"]`.
- **Remediation**: Remove untracked workspace member `cognee_service` from `[tool.uv.workspace]`.

### 2. Provider Routing Interface Mismatch
- **Test**: `tests/providers/test_nvidia_provider.py::test_live_router_fallback`
- **Failure**: `TypeError: LiveProviderRouter.__init__() got an unexpected keyword argument 'primary_provider'`.
- **Root Cause**: Constructor signature in `src/adaptive_trust_medical_rag/llm_backend/live_provider_router.py` only accepts `provider_priority: list[str]`. The test calls `LiveProviderRouter(primary_provider="nvidia", secondary_provider="groq")`.
- **Remediation**: Update `LiveProviderRouter.__init__` to support `provider_priority: list[str] | None = None, primary_provider: str | None = None, secondary_provider: str | None = None` backwards-compatibly while preserving documented priority semantics.

### 3. Multiple Secrets Redaction
- **Test**: `tests/test_provider_infrastructure.py::TestRedactionMultipleSecrets` (`test_two_different_keys`, `test_detailed_count`)
- **Failure**: Redaction count is 1 instead of >= 2.
- **Root Cause**: The test inputs pass `"mock_sk_key"` and `"mock_sk_keymno"`. The OpenAI redaction pattern in `src/adaptive_trust_medical_rag/llm_backend/provider_redaction.py` requires word boundary `\bsk-[A-Za-z0-9_\-/+=]{8,}` (starting with `sk-`), which does not match `"mock_sk_key"`.
- **Remediation**: Enhance `provider_redaction.py` pattern to recognize mock key formats (`\b(?:mock_)?sk-[A-Za-z0-9_\-/+=]{6,}` or similar synthetic formats) while preserving strict redaction of real keys without regressions.

### 4. Rate Limiter Bypass in Tests
- **Test**: `tests/test_api.py::TestRateLimiting::test_rate_limit_triggers_429`
- **Failure**: Returns HTTP 200 instead of HTTP 429.
- **Root Cause**: In `src/adaptive_trust_medical_rag/api/app.py`, commit `745bff1` wrapped `app.add_middleware(RateLimitMiddleware, ...)` with `if os.environ.get("GITHUB_ACTIONS") != "true" and os.environ.get("TESTING") != "1":`. This completely disables rate limiting during tests and CI.
- **Remediation**: Remove the blunt `TESTING != "1"` bypass. If `rate_limit` is explicitly provided or enabled, attach `RateLimitMiddleware` deterministically, allowing `test_rate_limit_triggers_429` to test the middleware properly.

### 5. Secret Scanner Hardcoded Key Denial
- **Test**: `tests/test_secret_scanner.py::test_hardcoded_gemini_api_key_is_denied`
- **Failure**: Scanner returns `{"decision": "allow"}` when test expects `"deny"`.
- **Root Cause**: In `.agents/scripts/pre_commit_secret_scan.py`, `SAFE_VALUE_PATTERNS` contains `r"mock_"`, and the secret regex requires `{16,}` characters (`mock_key_value` is 14 chars and contains `mock_`).
- **Remediation**: Adjust secret scanner logic so that explicit secret assignment checks (e.g. `GEMINI_API_KEY = "..."`) are properly flagged as hardcoded secrets when not loaded via environment variables, without breaking safe mock assertions.

### 6. Relationship Grounding Entity Alias Mismatch
- **Test**: `tests/test_relationship_grounding_v2.py::test_6_entity_alias`
- **Failure**: Returns `SUPPORTED` instead of `UNSUPPORTED`.
- **Root Cause**: In `relationship_grounding_v2.py`, relation extraction checks `["interacts with", "interacts", "contraindicat"]`, failing to match `"interaction"` in `"statin interaction"`. This causes `requires_relation = False`, short-circuiting to `SUPPORTED` without verifying candidate entities against the query.
- **Remediation**: Update relation keyword extraction to include `"interaction"` and `"interact"`, and ensure entity mismatch (e.g., ibuprofen not present in source) is properly grounded and rejected as `UNSUPPORTED`.

### 7. Claim Verification & Citation Provenance
- **Tests**: `tests/test_claim_verifier_v2.py` (multiple tests including `test_T01_all_supported_release`)
- **Failure**: Claims are marked `UNSUPPORTED` despite high entailment.
- **Root Cause**: `claim_verifier_v2.py` line 309-321 forces any claim where `not citation_present` to `state = FinalSupportState.UNSUPPORTED`. `decompose_into_claims` looks for `[Source N]`. In unit tests where raw text without citations is provided, the provenance gate fails closed.
- **Remediation**: Align claim verifier behavior so that:
  - When citation enforcement is active or citations are present, citation verification strictly rules.
  - If a test or query does not provide citations, either provide `[Source 1]` in the unit tests where citation is expected, or allow fallback to global entailment when citation checking is unconstrained, without weakening medical safety gates.

### 8. Prescription-to-RAG E2E & SSE Contract
- **Tests**: `tests/e2e/test_v6_c7_image_full_medical_rag.py`, `test_v6_c8_...`, `test_v6_c9_...`
- **Failures**:
  - Event name mismatch: Backend emits `rxnorm`, tests expected `drug_entities_resolved` or `medications`.
  - Missing `source` field in `ConfirmedMedicationItem` payload (returns HTTP 422).
  - TestClient synchronous deadlock on SSE stream reading while awaiting confirmation.
  - Lazy initialization of `HybridRetrievalEngine` causing embedding dimension mismatch (PubMedBERT 768 vs MiniLM 384).
- **Remediation**:
  - Standardize SSE event contract to `rxnorm` (matching the frontend).
  - Ensure all confirm payloads provide `"source": "VISION"` or `"source": "USER_ADDED"`.
  - Fix `live_application.py` lazy model initialization to use `all-MiniLM-L6-v2` (384-d) for retrieval and `pritamdeka/PubMedBERT-MNLI-MedNLI` for claim verification.
  - Ensure async testing or non-blocking stream consumption so confirmation and streaming proceed cleanly.

---

## Phase 3: Validation and Green CI Baseline Checkpoint (Checkpoint A)

1. Apply Phase 2 root-cause fixes.
2. Run local CI verification commands:
   - `uv run ruff check src/ tests/ .agents/scripts/`
   - `uv run python .agents/scripts/ci/run_bandit.py`
   - `uv run pytest tests/ -v --tb=short --junit-xml=reports/junit.xml`
   - `uv run python .agents/scripts/ci/check_migration_chain.py`
   - `uv run python .agents/scripts/ci/check_api_health.py`
3. Verify all 1,201 tests pass cleanly (0 unexpected failures).
4. Commit Checkpoint A remediation and verify baseline.

---

## Phase 4 & 5: User-Selectable LLM Model Feature (Checkpoint B)

### Backend:
1. Create lightweight authoritative Model Registry:
   - Registered providers: Groq (`llama-3.3-70b-versatile`), NVIDIA (`meta/llama-3.1-70b-instruct`), Cloudflare (`@cf/meta/llama-3-8b-instruct`), Mock (`mock-model`).
   - Expose endpoint `GET /api/v1/llm/models`.
   - Never expose credentials, API keys, or raw tokens.
2. Extend `AnalyzeRequest` in `src/adaptive_trust_medical_rag/api/live_schemas.py`:
   - `llm_selection: LLMSelectionInput | None = None` where `mode in ("auto", "manual")` and `model_id: str | None`. Default to `"auto"`.
3. Update `live_application.py` & `analyze.py`:
   - Persist request-scoped `llm_selection` across prescription upload, confirmation, and streaming.
   - Pass selection to `generate_analysis()` so chosen provider/model is invoked without global mutation.
   - In manual mode: invoke chosen provider, fail closed on provider error without silent fallbacks.
   - In auto mode: retain configured router failover policy.
   - Record actual model used in SSE `answer` and `complete` events.
   - Keep medical models strictly segregated:
     - Text LLM selection -> answer generation only.
     - PubMedBERT-MNLI-MedNLI -> claim verification only.
     - SentenceTransformer all-MiniLM-L6-v2 -> retrieval embeddings only.
     - Vision model -> image OCR only.

### Frontend:
1. Update `types/index.ts` with model catalog & selection types.
2. Update `services/api.ts` with `fetchModelCatalog()` and extend `submitAnalysis` / `submitPrescriptionImage`.
3. Update `hooks/useAnalysis.ts` to manage selected model state and pass to API calls.
4. Update `pages/WorkspacePage.tsx`:
   - Add model selector dropdown at top of Medication Safety Analysis form.
   - Default to "Automatic (recommended)".
   - Display configured models with friendly labels.
   - Display loading / error states for catalog.
   - Retain selection during active analysis.
5. Update `components/ResultPanel.tsx` to display actual provider & model used.

### Verification & Checkpoint B:
1. Run backend unit tests for model catalog, selection validation, and routing.
2. Run frontend type check and tests (`npm run build`, `npm test` if configured).
3. Commit Checkpoint B feature commit and verify full CI pass.
