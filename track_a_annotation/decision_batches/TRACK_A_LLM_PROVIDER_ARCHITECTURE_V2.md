# TRACK_A_LLM_PROVIDER_ARCHITECTURE_V2

## Redesigned Provider Landscape
The LLM execution layer has been redesigned away from a Gemini-centric approach. Instead, it relies on a standardized, provider-agnostic, OpenAI-compatible abstraction that natively supports:
* DIRECT_GROQ
* DIRECT_CLOUDFLARE
* DIRECT_HUGGINGFACE
* FREELLMAPI_GATEWAY

## Gateway vs Provider
A strict distinction is maintained between the **Gateway** (the routing endpoint receiving the request) and the **Provider** (the underlying hardware inference engine). For example, FREELLMAPI acts strictly as an API Gateway/Router. The underlying provider could be Groq or Cloudflare.

To preserve scientific reproducibility, any gateway routing metadata (such as x-freellmapi-provider and x-freellmapi-model-revision) is actively captured during inference to establish provenance.
