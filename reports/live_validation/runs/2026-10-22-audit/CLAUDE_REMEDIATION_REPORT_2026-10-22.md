# Live application remediation — 2026-10-22

Scope: the LLM provider failure, NVIDIA vision extraction, pipeline stage states, medication identity
labels, trust-score semantics, evidence provenance and citation links, shown in the 2026-10-22
screenshots. Research tool output only; nothing here is clinical advice.

Nothing was committed, pushed, tagged, merged or deployed. REL-LIVE-0003 was **not** approved.
No food-guidance evidence was activated. The frozen commits `baf6c93` and `30774eb` are untouched:
HEAD is `30774eb` on `ui/3d-redesign`, and `baf6c93` is its ancestor. All changes are uncommitted.

## 1. Baseline

| Item | Value |
|---|---|
| Branch / HEAD | `ui/3d-redesign` / `30774eb` |
| Working tree at start | Uncommitted Anti Gravity edits to `app.py`, `live_provider_router.py`, `openai_compatible_backend.py`, `.env.example`, plus unrelated modified research/report files (left untouched) |
| Other writers | A second agent edited the same tree during this work (its `live_audit.py`, `run_audit.ps1`, `start_servers.cmd`, `test_live_audit_regressions.py`, `EvidenceList.identity.test.tsx`, `vision_interfaces.model_used`). Its changes were kept and built on. |
| Baseline backend suite | 1470 passed, **4 failed**: 2 from the Anti Gravity router change, 2 frozen-hash checks |
| Servers at start | Not running (the earlier "started" log was not a running process). Later started by the other agent at 13:08 on 8000/5173. |

The 2 frozen-hash failures were line-ending drift in the working copy (git blob unchanged,
`git status` clean). They were fixed by re-materialising the two files from HEAD
(`FREE_REPLICATION_V1_MANIFEST.json`, `REAL_LLM_EVALUATION_PROMPT_V1_2.txt`). No content changed.

## 2. Root causes

Each cause below is **proven** by a live request or by code, unless it is marked as a hypothesis.

| Defect | Root cause | Evidence |
|---|---|---|
| NVIDIA LLM 404 | `nvidia/nemotron-3-super-120b-a12b` is in NVIDIA's catalog, but its backing function is "Not found for account". It is an account/model availability problem, not an outage. | Live `chat/completions` call: HTTP 404, detail "Function '…': Not found for account" |
| 404 misclassified | Anti Gravity mapped 404 to `TRANSIENT_PROVIDER`. The repo already had `provider_errors.classify_provider_error` mapping 404 to `MODEL_NOT_FOUND`; the adapter did not use it. | Code |
| Unsafe router change | Anti Gravity's router failed over on every `ModelExecutionError`, including `INVALID_REQUEST` and `UNKNOWN`. That broke 2 existing tests encoding "no failover for invalid requests". | Baseline test failures |
| Groq default model | Change C's default `llama-3.3-70b-versatile` is not available to this Groq account (HTTP 404 `model_not_found`). It was masked because `.env.local` still sets `GROQ_MODEL=openai/gpt-oss-120b`. The registry lists only `openai/gpt-oss-120b`, so the UI would also have marked Groq unavailable. | Live `/models` and chat call |
| Env loading | `load_dotenv(".env.local")` used a working-directory-relative path, so the configuration depended on where uvicorn was started. | Code |
| Ignored settings | `LLM_PRIMARY_PROVIDER`, `LLM_FALLBACK_PROVIDER=gemini` and `CLOUDFLARE_ENABLED=false` are not read by the live router. Gemini has no live adapter. | Code; now warned at startup |
| NVIDIA vision timeout | **Intermittent stalled requests at NVIDIA, not a malformed request.** In 10 direct calls (same model, synthetic image), 9 returned HTTP 200 in 1.6–11.5 s and 1 never responded within 120 s. Through the app's HTTP/SSE path, 5 of 5 extractions succeeded in 7.1–12.6 s. A longer timeout would not help a stalled request. The 45 s limit in the screenshot was introduced by this session (the original was 60 s). | `claude_remediation_artifacts/nvidia_vision_latency_samples.json`; HTTP runs below. *Hypothesis:* your failed request was such a stall. Its backend log was not available to confirm it. |
| User Confirmation shown green after failed extraction | `PipelineProgress.getStageStatus`: `confirmed = stageKey === 'confirming' && updates.some(u => u.stage === 'extracting')`. Any extraction update, including `failed`, marked confirmation complete. | Code |
| Failed-stage update could be lost | On a vision failure the backend sent the terminal `error` before `extracting: failed`; the client closes the stream on `error`. | Code |
| "Not run" for manual entry | Inapplicable image stages used the same "skipped" state as stages stopped by an error. | Code |
| Medication "Verified" | The badge meant "RxCUI resolved", not evidence. Also, the entity cache returned every hit as `source=cache`, `confidence=1.0`, so an **approximate** RxNorm match stored at runtime was later shown as certain. | Code |
| Trust score 0.00 | The score is the maximum over chunks that reached scoring. When none did, it was reported as a computed `0.0`. | Code |
| "11 unrelated chunks" | The live corpus has 14 chunks and retrieval uses `top_k=20`, so every search returns the whole corpus. 3 chunks name lisinopril; 11 are about other drugs and are correctly excluded by the medication-alignment gate. This is corpus size, not a ranking defect. | Live `retrieval` event: `evidence_count=14, corpus_chunk_count=14, top_k=20` |
| Placeholder DailyMed records | All 11 DailyMed records in `LIVE_MEDICAL_CORPUS_V2` are hand-authored text with `setid=example-*` URLs, carrying authority 0.95 / freshness 0.9 that were never earned. | Corpus file |
| PMID 31234567 | PubMed esummary (2026-10-22): *"Assessment of the Spatial Distribution of Moisture Content in Granular Material Using Electrical Impedance Tomography"*, Sensors (Basel) 2019. The corpus attaches it to two unrelated documents: "Lisinopril and Potassium Supplements" and "Food Interactions with Oral Antineoplastics". Both associations are misattributed. | Live NCBI esummary |
| Scores used without identity | Unverified chunks fed their stored authority into trust scoring and appeared as `provenance_status: "RETRIEVED"`. `verified_source_links` was never populated in production, so no source was ever identity-verified. | Code |
| Spironolactone claims could never verify | The claim-identity extractor's fixed drug pattern does not match "spironolactone", so no lisinopril + spironolactone claim could get a relationship identity. | Code |
| Confirmation timeout | When the user did not confirm in time, the stream ended with no terminal event. | Code |

## 3. Changes (all uncommitted)

**Provider routing and configuration**
- `llm_backend/live_provider_router.py`: explicit `FAILURE_POLICY` per failure class, with retry and failover decided separately. MODEL_NOT_FOUND, auth and malformed output fail over with no retry. Invalid request, application-semantic and unknown errors neither retry nor fail over. Transient errors get one bounded retry with backoff and jitter, only on the last provider. Rate limits wait only within a Retry-After of 10 s or less. There is one shared request deadline (cancels the hanging call), an attempt log per request (provider, model, class, decision, elapsed), and `ALL_PROVIDERS_FAILED` keeps every attempt. A direct user selection gets one attempt.
- `llm_backend/openai_compatible_backend.py`: uses the shared classifier. 404 maps to MODEL_NOT_FOUND with the model ID named; Groq `json_validate_failed` maps to SCHEMA_ERROR; Retry-After is parsed; error bodies are redacted and truncated; the timeout is configurable.
- `api/app.py`: `.env.local` then `.env` load from the repo root (precedence: process env > `.env.local` > `.env`). `build_llm_router()` registers only credentialed providers. `LLM_PROVIDER` / `LLM_FALLBACK_PROVIDERS` / `LLM_FAILOVER_ENABLED` / `LLM_REQUEST_DEADLINE_S` / `*_TIMEOUT_S` are supported. The Groq default goes back to `openai/gpt-oss-120b`, verified available. The order and models are logged at startup with no secrets.

**Vision**
- `llm_backend/openai_vision_backend.py`: 30 s per attempt (about 2.6× the slowest success observed), **one immediate retry of the same model** for timeout, network or 5xx, then the optional `VISION_FALLBACK_MODEL` for availability failures, all inside a 75 s total deadline (`VISION_TIMEOUT_S`, `VISION_DEADLINE_S`). HTTP errors are classified (404/403/4xx/5xx). Each attempt logs model, status, duration, image size and NVIDIA `nvcf-reqid`, never the key, image or text. The model and endpoint are unchanged (`meta/llama-3.2-11b-vision-instruct` at `integrate.api.nvidia.com/v1/chat/completions`), and there is no text-only fallback.
- `services/live_application.py`: `extracting: failed` is sent before the terminal error. The error carries `failure_class`, attempts and a next step. There is an explicit `CONFIRMATION_TIMEOUT` (300 s). The reported vision model is the one that answered.

**Evidence and claims**
- `services/live_source_links.py`: a source-identity status (`VERIFIED` / `UNVERIFIED` / `REJECTED_SOURCE_IDENTITY`) and `check_source_identity()`. An identity record must be complete, match the URL, resolve its own set ID or PMID, and is never satisfied by a placeholder or a shared URL.
- `services/live_application.py`: **hard identity gate** before any scoring. Non-verified chunks are excluded (listed in `excluded_sources` with a reason) and never reach the model. Duplicate content counts once. Evidence items carry `source_identity_status`, `provenance_status: CONTENT_HASH_MATCHED`, title, external ID, version and `claim_support_status`. The trust score is `null` with `score_status: NO_ELIGIBLE_EVIDENCE` when nothing reached scoring. The `retrieval` event adds `corpus_chunk_count` and `top_k`. Medications carry `identity_method`.
- `verification/canonical_identity.py`: `RequestDrugMap`, opt-in on the live path only, so the request's own normalised names (e.g. spironolactone) are recognised in claims. Research callers pass plain dicts and their results are unchanged.
- `normalization/entity_cache.py`, `drug_normalizer.py`: cache entries keep the resolver and confidence they came from. Seed entries are `seed_cache`.

**Frontend**
- `PipelineProgress.tsx`: each stage comes from its own update. Confirmation is complete only after a completed extraction and a later backend stage. Manual entry shows "Not applicable" for the image-only stages. Relationship Verification reports with Claim Verification. The mode used is the running analysis's (`useAnalysis.runInputMode`).
- `MedicationCard.tsx`: "Identity resolved" (not "Verified"), the method (RxNorm exact / approximate / curated mapping, "(cached)"), and "Drug identity only".
- `EvidenceList.tsx`, `services/evidenceDisplay.ts`: identity badges (verified / not verified / rejected), "Supports a verified claim", source title, ID and version, an excluded-sources list, a note on what the scores mean, and links only for verified sources at an allowlisted https evidence host (no placeholder set IDs, credentials or other schemes). Links open with `target=_blank rel="noopener noreferrer"`.
- `TrustSummary.tsx`, `SecurityChecks.tsx`, `EvidencePage.tsx`: "Not computed (no eligible evidence)" instead of 0.00.

**Evidence candidate (pending)**
- `scripts/build_rel_live_0003_candidate.py` → `rel_live_0003_candidate/` (this folder, **not** `data/live_medical/relationships/`, as with REL-LIVE-0002).
- Source: lisinopril tablet SPL, set ID `34ebeea1-6812-4697-84c4-b2ae4f39e55f` (Bluepoint Laboratories), version 12, published Oct 09, 2026, section **7.1 Diuretics**, verbatim. It names spironolactone among potassium-sparing diuretics that "can increase the risk of hyperkalemia" and asks for frequent serum-potassium monitoring.
- RxCUIs checked with RxNav: 29046 lisinopril, 9997 spironolactone.
- Content hash `8a9bde7f5d84…`; records SHA `47a26a0dfe1e…`; evidence SHA `5cae35c0e003…`.
- Predicate INTERACTION, BIDIRECTIONAL. **Severity `UNGRADED`.** A `MAJOR` value set earlier was removed because no documented severity method was applied. An UNGRADED record is rejected by the loader even if approved. The revision history is in the manifest.
- Status `CANDIDATE_PENDING_RESEARCHER_APPROVAL`. Section 5.1 of the spironolactone label (set ID `768563dc-…`) only names the ACE-inhibitor class, so it is not pair-specific and is not used.
- No food-guidance candidate was prepared.

**Tests updated (assertions changed, with reason)**
- Fixtures for post-generation tests declare their synthetic chunks identity-verified (commented as a fixture assumption). Without that they now, correctly, stop at the identity gate.
- `test_evidence_with_an_unverified_url…` now asserts exclusion before generation. Two `overall_score == 0.0` assertions are now `None`.
- `test_5_malicious_image…` confirms before streaming. The old order relied on the silent timeout re-running vision.
- The other agent's `test_the_extraction_names_the_model…` scenario now uses two timeouts (retry policy). The candidate path moved.

## 4. Results

### Real provider and HTTP/SSE runs (no mocks; real NVIDIA, Groq, RxNav, embeddings, NLI)

| Check | Result |
|---|---|
| Groq `openai/gpt-oss-120b` minimal inference | PASSED: HTTP 200, `{"ok":true}`, about 1 s |
| Real failover through `build_llm_router()` with `LLM_PROVIDER=nvidia` | PASSED: nvidia 404 → `MODEL_NOT_FOUND`, decision `failover`, 0.6 s, no retry. Groq served in 0.9 s. |
| NVIDIA vision, direct, 10 sequential calls | 9 PASSED (1.6–11.5 s), 1 stalled (no response within 120 s) |
| NVIDIA vision through the app (port 8000, earlier code), 4 runs | PASSED 4/4: both drugs HIGH, 7.1–10.5 s (25 KB PNG and 1.7 MB JPEG) |
| **Text mode** HTTP/SSE, new code (port 8001), lisinopril + spironolactone | PASSED (expected abstention): RxNorm 29046 `seed_cache`, 9997 `rxnorm_exact`; 14 retrieved (whole corpus), 11 unrelated, 3 rejected (SPL-LISINOPRIL-001/002 PLACEHOLDER, PMID-31234567 SHARED); score `null` / `NO_ELIGIBLE_EVIDENCE`; no model called; one terminal event |
| **Image mode** HTTP/SSE, new code, synthetic prescription | PASSED: NVIDIA 11b extracted both drugs HIGH in 12.0 s (1 attempt); confirmation posted; backend resumed with `uploading` → `normalizing`; same identity gate and abstention as text mode |
| Lisinopril + spironolactone answer with authentic evidence, real NLI | PASSED **in a test only** (candidate approved in a temp dir with a test-only severity): claim SUPPORTED, identity MATCH, PubMedBERT entailment 0.9996, link opens the exact DailyMed set ID. **Not available in the application** until REL-LIVE-0003 is graded and approved. |

Artifacts: `claude_remediation_artifacts/` (SSE payloads, latency samples, the synthetic image).

### Automated suites

| Command | Result |
|---|---|
| `TESTING=1 uv run pytest -q` (whole backend) | **PASSED: 1565 passed, 0 failed** (NLI is a keyword mock under `TESTING=1`) |
| `uv run pytest tests/e2e/test_live_evidence_provenance.py` without `TESTING` (real PubMedBERT NLI) | PASSED: 17 |
| New: `tests/test_live_provider_failover_policy.py` | PASSED: 28 (fake adapters) |
| New: `tests/providers/test_vision_fallback_and_timeouts.py` | PASSED: 17 (simulated HTTP) |
| New: `tests/e2e/test_live_evidence_provenance.py` | PASSED: 17 (Tests J, K, L, M, N, O and F at pipeline level) |
| `npx vitest run` (frontend) | **PASSED: 19 files, 123 tests** (new: stage states, identity labels, uncomputed score, link safety) |
| `npx tsc -b`, `npm run build` | PASSED |
| `npm run lint` | PASSED: 0 errors, 3 warnings (the freeze baseline count; none new) |
| `uv run ruff check src tests …` | PASSED |
| `uv run bandit -q -r src -ll` | PASSED (exit 0) |
| `verify_v3_1_integrity.py`, `verify_v3_confirmed_separation.py` | PASSED |
| `gitleaks` over the uncommitted diff and the changed directories | PASSED: no leaks |
| Frozen-hash reproducibility tests | PASSED (in the full suite) |

### Not run / blocked

| Check | Status | Why / how to run |
|---|---|---|
| Browser check of the new UI | NOT RUN | Your servers on 8000/5173 were started at 13:08, before the backend changes, and were left running. Restart them (`reports\live_validation\runs\2026-10-22-audit\start_servers.cmd` after closing both windows), then open http://127.0.0.1:5173. |
| Reproducing your specific 45 s failure | BLOCKED | Your backend's console log was not readable from here. The latency data supports a stalled-request cause; the new retry handles it. |
| Linux checkout | NOT RUN | Windows only. |
| Food-guidance candidate | NOT RUN | Not prepared; nothing activated. |

## 5. Remaining risks

1. **No evidence-backed answer is possible in the live app yet.** No chunk of the frozen corpus has a verified source identity, and REL-LIVE-0003 is pending and ungraded. Every interaction analysis abstains before generation, so Groq is never called through the pipeline in production. This is the intended safe state, not a defect.
2. NVIDIA LLM is unusable for this account (404) until NVIDIA enables the function or `NVIDIA_LLM_MODEL` names an available model. Every automatic request costs one fast 404 before Groq serves.
3. Vision stalls can still exhaust both attempts (about 60 s) on a bad NVIDIA day. The user then gets a classified error with a next step, never a medication list.
4. Severity grading for REL-LIVE-0003 needs the project's documented method, which this audit did not find.
5. The live corpus (14 synthetic chunks) cannot support retrieval-precision evaluation. Corpus replacement through approved V2 records is the path.
6. `.env` and `.env.local` disagree (`LLM_PROVIDER`, `GROQ_MODEL`). The precedence is now documented and logged; consider removing the stale values.
