# Provider Capability Matrix

> [!NOTE]
> Each capability is labeled as **DOCUMENTATION-DERIVED** or **EMPIRICALLY VERIFIED**.
> Documentation-derived entries reflect published provider documentation as of September 2026.
> They do NOT constitute empirical benchmark results.

## Matrix

| Capability | Groq (`openai/gpt-oss-120b`) | Gemini (`gemini-3.1-pro-preview`) | Hugging Face (configurable) | Cloudflare Workers AI |
|---|---|---|---|---|
| **Provider** | Groq | Google AI | HF Inference Providers | Cloudflare Workers AI |
| **Model ID** | `openai/gpt-oss-120b` | `gemini-3.1-pro-preview` | `meta-llama/Llama-3.3-70B-Instruct` (default) | `@cf/meta/llama-3.3-70b-instruct-fp8-fast` (candidate) |
| **Context Window** | 131,072 tokens (DOC-DERIVED) | 1M tokens (DOC-DERIVED) | Model-dependent (DOC-DERIVED) | 24K tokens (DOC-DERIVED) |
| **Maximum Output** | 65,536 tokens (DOC-DERIVED) | Model-dependent (DOC-DERIVED) | Model-dependent (DOC-DERIVED) | Model-dependent (DOC-DERIVED) |
| **Structured Output** | JSON Schema mode (DOC-DERIVED) | Structured output API (DOC-DERIVED) | Model-dependent (DOC-DERIVED) | Limited (DOC-DERIVED) |
| **Tool/Function Calling** | Yes (DOC-DERIVED) | Yes (DOC-DERIVED) | Model-dependent (DOC-DERIVED) | Yes, select models (DOC-DERIVED) |
| **Streaming** | Yes (DOC-DERIVED) | Yes (DOC-DERIVED) | Yes (DOC-DERIVED) | Yes (DOC-DERIVED) |
| **Reasoning** | Yes (DOC-DERIVED) | Yes (DOC-DERIVED) | Model-dependent (DOC-DERIVED) | Model-dependent (DOC-DERIVED) |
| **Rate Limit Visibility** | Full headers: `x-ratelimit-*` (EMPIRICALLY VERIFIED) | HTTP 429 with retry info (EMPIRICALLY VERIFIED) | Limited (DOC-DERIVED) | Neuron-based quota (DOC-DERIVED) |
| **Free Tier** | Developer plan with finite limits (DOC-DERIVED) | Free tier with quota limits (EMPIRICALLY VERIFIED: 429 QUOTA_EXHAUSTED) | ~$0.10/month free credits (DOC-DERIVED) | 10,000 Neurons/day free (DOC-DERIVED) |
| **Free Allocation** | Finite RPM/RPD per model (DOC-DERIVED) | 0 remaining on current key (EMPIRICALLY VERIFIED) | $0.10/month, subject to change (DOC-DERIVED) | 10,000 Neurons/day (DOC-DERIVED) |
| **Credential Required** | `GROQ_API_KEY` | `GEMINI_API_KEY` | `HF_TOKEN` | `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` |
| **Fallback Eligible** | Yes (transient failures only) | Yes (transient failures only) | Yes, when tertiary enabled (transient only) | Yes, when cloudflare_enabled (transient only) |
| **Scientific Mode Eligible** | No | Yes (frozen Phase 15 provider) | No | No |
| **Development Mode Eligible** | Yes (primary) | Yes (secondary) | Yes (quaternary fallback) | Yes (tertiary, when enabled) |
| **Implementation Status** | ✅ IMPLEMENTED | ✅ IMPLEMENTED | ✅ IMPLEMENTED | ✅ IMPLEMENTED |
| **OpenAI Compatible** | Yes (native) | No (Gemini SDK) | Model-dependent | Yes (DOC-DERIVED) |
| **Evidence Type** | Mixed | Mixed | DOCUMENTATION-DERIVED | DOCUMENTATION-DERIVED |

## Runtime Observations

| Provider | Observation | Classification |
|---|---|---|
| Gemini | `429 RESOURCE_EXHAUSTED` on free-tier key | `GEMINI_RUNTIME_QUOTA_EXHAUSTED` — account/key-specific, not a general Gemini unavailability claim |
| Groq | Credential present, not yet connectivity-tested in this iteration | `GROQ_CREDENTIAL_PRESENT` |
| Hugging Face | Not yet connectivity-tested | `HF_NOT_TESTED` |
| Cloudflare | Backend not implemented | `CLOUDFLARE_BACKEND_NOT_IMPLEMENTED` |

## Important Distinctions

> [!WARNING]
> **Documentation-derived ≠ empirically verified.** Structured output, tool calling, and streaming capabilities listed above reflect provider documentation. They do not establish equivalent model behavior across providers.

> [!WARNING]
> **Free tier ≠ guaranteed free usage.** HF free credits are ~$0.10/month and are subject to change. Cloudflare's 10,000 Neurons/day is a compute quota, not unlimited inference. Groq developer-plan limits are finite. These are operational constraints, not guarantees.

> [!IMPORTANT]
> **Groq structured-output constraints.** Groq documents JSON Schema and tool use for `openai/gpt-oss-120b`, but has specific constraints around combining structured outputs with streaming/tool calls. The capability matrix records this as a documentation-derived capability contract, not proof of equivalent behavior to Gemini's structured output.
