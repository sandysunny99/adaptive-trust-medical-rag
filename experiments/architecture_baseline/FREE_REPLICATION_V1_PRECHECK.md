# Free Replication V1 Precheck (FINAL)

## 1. Experiment Identity
* **Track:** `FREE_REPLICATION_V1`
* **Purpose:** Controlled evaluation of the RAG security architecture using a zero-cost API provider.

## 2. Provider/Model Identity
* **Primary Provider:** `groq`
* **Primary Model:** `openai/gpt-oss-120b`

## 3. Canonical Phase 15 Separation
* Canonical Phase 15 remains FROZEN (`gemini-3.1-pro-preview`) and currently BLOCKED by `GEMINI_FREE_TIER_UNAVAILABLE`.
* `FREE_REPLICATION_V1` possesses its own unique Protocol, Configuration, and Manifest.

## 4. Model Capability Checks (Groq `openai/gpt-oss-120b`)
* **PROVIDER_SMOKE_TEST:** PASS
* **PROJECT_ORCHESTRATOR_TOOL_PATH:** PASS (Verified via native text action parsing, sync adapter, and AuthorizationBoundary).
* **STRUCTURED_OUTPUT_PROVIDER_CAPABILITY:** PASS
* **STRUCTURED_EXTRACTION_REQUIRED_BY_REPLICATION:** NO
* **REAL_SECURITY_PATH:** PASS
* **REAL_AUTHORIZATION_PATH:** PASS
* **REAL_TOOL_EXECUTOR:** PASS
* **SYNC_ADAPTER_VALIDATION:** PASS
* **REGRESSION_TESTS:** PASS
* **TRACEABILITY:** PASS

## 5. Token/Capacity Planning
* **TOKEN_ESTIMATE_METHOD:** STATIC_ESTIMATE (3,500 tokens/call planning assumption).
* **ACTUAL_SYNTHETIC_MODEL_CALLS:** 1 per condition (baseline/hardened).
* **ACTUAL_SYNTHETIC_TOTAL_TOKENS:** ~392 (observed in smoke test — not representative of full RAG workload).
* **STATIC_TOKEN_ESTIMATE (Full Context):** ~3,500 tokens per condition.
* **CALL_COUNT_ACCOUNTING:** PASS — derived from orchestrator code path analysis and actual benchmark family distribution.

### Family-Specific Call Patterns (200 cases)
| Family | Count | Baseline | Hardened | Reason |
|---|---|---|---|---|
| `PROMPT_INJECTION` | 35 | 1 call | 0 calls | Hardened: blocked before LLM by PromptInjectionDetector |
| `RETRIEVAL_POISONING` | 35 | 1 call | 0–1 calls | Hardened: may abstain at evidence eligibility gate due to high poisoning risk |
| `BOUNDARY_VIOLATION` | 35 | 1 call | 1 call | Hardened: LLM generates action, but AuthorizationBoundary blocks it post-gen |
| `UNSUPPORTED_CLAIM` | 35 | 1 call | 0–1 calls | Hardened: may abstain at evidence eligibility gate if chunks are rejected |
| `CONTRADICTION` | 30 | 1 call | 0–1 calls | Hardened: may abstain at evidence eligibility gate or answer safety gate |
| `BENIGN_CONTROL` | 30 | 1 call | 1 call | Full pipeline traversal |

### Aggregated Estimates
* **BASELINE_CALLS:** 200
* **HARDENED_CALLS_EXPECTED_RANGE:** 65–165
* **EXPECTED_MODEL_CALLS:** 265–365
* **WORST_CASE_MODEL_CALLS:** 730 (with retry budget).
* **EXPECTED_TOKENS:** ~927,500 – 1,277,500 (265-365 × 3,500).
* **WORST_CASE_TOKENS:** ~2,555,000 (730 × 3,500).
* **EXPECTED_DURATION:** ~6–8 days (at 180K TPD safety budget).
* **WORST_CASE_DURATION:** ~15 days.

## 6. Groq Limit Analysis & Accounting
* **GROQ_TPM_LIMIT:** 8,000
* **GROQ_TPD_LIMIT:** 200,000
* **GROQ_RPM_LIMIT:** 30
* **GROQ_RPD_LIMIT:** 1,000
* **QUOTA_ACCOUNTING:** PASS (Attempted vs Committed resource accounting split).
* **CHECKPOINT_RESUME:** PASS (Demonstrated via real runner synthetic implementation).
* **CRASH_RECOVERY:** PASS (Demonstrated atomic pair commits with zero active duplicate baselines).
* **ACTIVE_PAIR_INTEGRITY:** PASS
* **ACCOUNTING_INTEGRITY:** PASS

## 7. Cloudflare & NVIDIA Backup 
* Retained as secondary backups.

## 8. Reproducibility & Protocol Freeze
* **Pass:** Fixed provider `groq`, fixed model `openai/gpt-oss-120b`, disabled failover.
* **PROTOCOL_FREEZE_ELIGIBILITY:** PASS
* **NEW_PROTOCOL_FROZEN:** YES

## 9. Next Steps
Await authorization to execute FREE_REPLICATION_V1 Credentialed Preflight on a test subset.
