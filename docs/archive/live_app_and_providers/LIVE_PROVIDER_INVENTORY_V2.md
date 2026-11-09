> **WARNING: HISTORICAL / SUPERSEDED BY V3**
> This document is maintained for research provenance. For the current LIVE application provider status, refer to the V3 documents.

# Live Provider Inventory

| Provider | Credential | Endpoint | Model | Adapter Exists | Router Registered | Health Check | Live Tested | Status |
|---|---|---|---|---|---|---|---|---|
| Groq | `GROQ_API_KEY` | `api.groq.com/openai/v1` | `openai/gpt-oss-120b` | Yes (`OpenAICompatibleBackend`) | Yes | Supported | Yes (861ms) | CONFIGURED AND INTEGRATED |
| NVIDIA NIM | `NVIDIA_API_KEY` | `integrate.api.nvidia.com/v1` | `nvidia/nemotron-3-super-120b-a12b` | Yes (`OpenAICompatibleBackend`) | Yes | Supported | Yes (200 OK) | CONFIGURED AND INTEGRATED |
| Hugging Face | `HF_TOKEN` | `api-inference.huggingface.co/models/...` | `meta-llama/Llama-3.3-70B-Instruct` | Yes (Legacy `HuggingFaceBackend`) | Yes (Incompatible Interface) | Not natively | No | CONFIGURED BUT INCOMPATIBLE ADAPTER |
| Cloudflare AI | `CLOUDFLARE_API_TOKEN` & `ACCOUNT_ID` | `api.cloudflare.com/client/v4/accounts/...` | `@cf/meta/llama-2-7b-chat-int8` | Yes (Legacy `CloudflareBackend`) | Yes (Incompatible Interface) | Not natively | No | CONFIGURED BUT INCOMPATIBLE ADAPTER |
| FreeLLM API | MISSING | `api.freellmapi.com/v1/chat/completions` | `UNKNOWN` | Yes (`PilotAdapter`) | No | N/A | No | NOT CONFIGURED |

*Note: While `HuggingFaceBackend` and `CloudflareBackend` exist, they currently implement an older `ModelGenerationResult` interface rather than the standard `ProviderAdapter` and `ProviderResponse` interface with `generate_structured()` required by `LiveProviderRouter`.*
