# Provider Selection Evidence

## Provider Matrix

| Provider | Model | Adapter | Factory path | Credential variable | Credential presence | Dependency | Interface | Reproducibility | Security boundary | Replication readiness | Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Groq | openai/gpt-oss-120b | groq_backend.py | __init__.py | GROQ_API_KEY | LOCAL_CREDENTIAL_PRESENT | READY | GAP | PARTIAL | PASS | BLOCKED | PROVISIONAL | config.py default |
| Cloudflare | @cf/meta/llama-3.3-70b-instruct-fp8-fast | cloudflare_backend.py | __init__.py | CLOUDFLARE_API_TOKEN | LOCAL_CREDENTIAL_PRESENT | READY | GAP | PARTIAL | PASS | BLOCKED | CANDIDATE | Secondary |
| HuggingFace | meta-llama/Llama-3.3-70B-Instruct | huggingface_backend.py | __init__.py | HF_TOKEN | LOCAL_CREDENTIAL_PRESENT | MISSING | GAP | PARTIAL | PASS | BLOCKED | CANDIDATE | Tertiary |
| Gemini | gemini-3.1-pro-preview | google_gemini_backend.py | __init__.py | GEMINI_API_KEY | LOCAL_CREDENTIAL_PRESENT | READY | GAP | PARTIAL | PASS | BLOCKED | FROZEN_PHASE15 | Phase 15 Freeze |

**Conclusion**: Groq is designated as the PROVISIONAL candidate because it holds Priority 1 in RoutingConfig.default_routing(). No final research decision has been made; it is an engineering target for Gate C connectivity.