# Free Provider Access Matrix & Replication Track

> [!IMPORTANT]
> The canonical Phase 15 experiment is currently BLOCKED due to a zero-quota Free-Tier restriction on the exact frozen model. This document establishes a **new, scientifically isolated** research track to conduct a free-provider replication. Canonical Phase 15 is NOT modified.

## 1. Executive Summary

The objective is to determine whether the security architecture can be evaluated reproducibly under a no-payment provider configuration. Groq and Cloudflare Workers AI present the strongest current candidates due to existing, functional credentials in the project and documented free capabilities. A new, isolated experiment (`FREE_REPLICATION_V1`) will be created to test this, ensuring the canonical Phase 15 Gemini Pro experiment remains frozen.

## 2. Canonical Phase 15 Frozen State

```text
PHASE15_STATUS                 = FROZEN / NOT_STARTED
PHASE15_PROVIDER               = gemini
PHASE15_MODEL                  = gemini-3.1-pro-preview
PHASE15_FAILOVER               = DISABLED
PHASE15_PROVIDER_IMMUTABLE     = TRUE
PHASE15_EXECUTION_STARTED      = NO
PHASE15_API_CALLS              = 0
PHASE15_OBSERVATIONS           = 0
```

## 3. Current Gemini Limitation

The project lacks a paid Google Cloud Billing account, and Google's documentation explicitly indicates that `gemini-3.1-pro-preview` has zero allocation on the Gemini API Free Tier. This is a provisioning blocker (`GEMINI_FREE_TIER_UNAVAILABLE`), not an experimental failure.

---

## 4. Groq Access / Capability

*   **Credential / Connectivity:** `GROQ_API_KEY` present. Smoke test: **PASS**
*   **Candidates:** `openai/gpt-oss-120b`, `openai/gpt-oss-20b`
*   **Context:** 131,072 tokens
*   **Structured Output:** Soft JSON mode
*   **Tool Calling:** Supported
*   **Reasoning:** Supported
*   **Limits:** 30 RPM, 1,000 RPD, 8,000 TPM
*   **Access Status:** RECURRING_FREE (Developer tier)

## 5. Cloudflare Access / Capability

*   **Credential / Connectivity:** `CLOUDFLARE_API_TOKEN` present. Smoke test: **PASS**
*   **Candidates:** `@cf/meta/llama-3.3-70b-instruct-fp8-fast`, `@cf/nvidia/nemotron-3-120b-a12b`, `@cf/google/gemma-4-26b-a4b-it`
*   **Context:** Up to 24,000 tokens (model dependent)
*   **Structured Output:** Best-effort JSON
*   **Tool Calling:** Supported
*   **Limits:** 10,000 Neurons/day
*   **Access Status:** RECURRING_FREE

## 6. Cerebras Access / Capability

*   **Credential:** NOT CONFIGURED
*   **Candidates:** `gpt-oss-120b`, `qwen-3-235b-a22b-instruct-2507`, `llama3.1-8b`
*   **Limits:** High rate ceilings documented
*   **Access Status:** LIMITED_FREE_CREDITS (Promotional trial credits, not perpetual)

## 7. NVIDIA Access / Capability

*   **Credential:** NOT CONFIGURED
*   **Candidates:** Nemotron, DeepSeek, Kimi
*   **Access Status:** RECURRING_FREE (Developer Program / API Catalog for prototyping)

## 8. Hugging Face Access / Capability

*   **Credential / Connectivity:** `HF_TOKEN` present. Smoke test: **FAIL** (ConnectionError)
*   **Limits:** $0.10/month inference-provider credits
*   **Access Status:** INSUFFICIENT_FREE_CAPACITY

## 9. OpenRouter Access / Capability

*   **Candidates:** `openrouter/free` (and specific pinned free models)
*   **Scientific Control:** ROUTER_DYNAMIC_MODEL = NOT SCIENTIFICALLY_CONTROLLED (Unless model is pinned exactly)

## 10. Gemini Flash Free Candidates

*   **Candidates:** `gemini-3.5-flash`, `gemini-3.1-flash-lite`, etc.
*   **Limits:** e.g., 15 RPM, 1M TPM, 1,500 RPD
*   **Access Status:** RECURRING_FREE
*   *Note: Cannot be used as Phase 15 substitutes. Candidate for free replication only.*

## 11. Additional Provider Candidates

*   **SambaNova:** Free tier available, 1M TPM
*   **Mistral:** Free tier available

---

## 12. Capacity Analysis

*   **Experiment:** N = 200 cases x 2 conditions (Baseline/Hardened)
*   **Nominal Generation Requests:** 400
*   **ESTIMATED_MODEL_CALLS:** >400 (If orchestrator performs internal tool calls, context validation, or JSON schema repair retries, the multiplier will increase. E.g., 1 generation + 1 evidence-gate evaluation = ~800+ calls total).
*   **Bottleneck:** Groq's 8,000 TPM limit requires aggressive pacing/backoff (e.g., waiting ~30s between queries). Cloudflare's 10,000 Neurons/day limit would strictly span multiple days for 400 cases.

## 13. Scientific-Control Analysis

To qualify for controlled replication, the provider must support:
*   Fixed model identifier
*   Fixed provider configuration
*   Deterministic experiment manifest
*   Reproducible output capture

Dynamic routers (like unpinned OpenRouter paths) fail this requirement.

## 14. Provider Eligibility Matrix

| Provider | Access | Free Status | RAG Capabilities (Context/Tools) | Reproducible | Eligible for Replication? |
|---|---|---|---|---|---|
| **Groq** | Configured | RECURRING_FREE | High | YES | **YES** (Primary) |
| **Cloudflare** | Configured | RECURRING_FREE | Med | YES | **YES** |
| **NVIDIA NIM**| Unconfigured | RECURRING_FREE | High | YES | YES |
| **Gemini Flash**| Unconfigured | RECURRING_FREE | High | YES | YES |
| **Cerebras** | Unconfigured | LIMITED_FREE_CREDITS| High | YES | NO (Non-perpetual) |
| **Hugging Face**| Configured | INSUFFICIENT_CAPACITY| Med | YES | NO |
| **OpenRouter (Dyn)**| Unconfigured| RECURRING_FREE | Varies | NO | NO |

---

## 15. Proposed FREE_REPLICATION_V1

Do NOT modify Phase 15.
Create a new experimental definition:

*   **Experiment ID:** `FREE_REPLICATION_V1`
*   **Protocol ID:** `protocol_free_rep_v1`
*   **Configuration ID:** `config_groq_120b` (if Groq is selected)
*   **Provider:** `groq`
*   **Model:** `openai/gpt-oss-120b`
*   **Dataset Reference:** Re-use 200 Phase 15 input fixtures mapped to the new runner.
*   **Comparison:** Condition A (Baseline) vs Condition B (Hardened)

## 16. Risks and Limitations

*   **Groq TPM Constraints:** The 8,000 TPM limit on Groq's free tier requires extreme rate-limit pacing.
*   **Different Model Behavior:** Groq's `gpt-oss-120b` may exhibit significantly different semantic compliance, abstention thresholds, and reasoning styles than Gemini 3.1 Pro. The result answers a parallel scientific question about architecture robustness, not the original canonical hypothesis.

## 17. Exact Next Action

*   Select ONE primary free-provider replication (Recommendation: Groq `openai/gpt-oss-120b`).
*   Draft the `FREE_REPLICATION_V1` isolated protocol and manifest.
*   Execute Track A (Human Annotation) independently.
*   Keep Canonical Phase 15 frozen.
