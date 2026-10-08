# Live Provider Inventory V3

## Current Configured Providers

| Provider | Role | Status | Note |
|---|---|---|---|
| **Groq** | Primary | Active | Configured via OpenAICompatibleBackend |
| **NVIDIA** | Secondary | Active | Configured via OpenAICompatibleBackend |
| **Cloudflare** | Tertiary | Active | Newly integrated via OpenAICompatibleBackend |
| **Hugging Face** | None | Excluded | Network/DNS failures, structured output unreliability |
| **FreeLLM** | None | Excluded | Not a single provider, just a catalog |

## Conclusion
The live application utilizes a highly resilient three-provider architecture.
