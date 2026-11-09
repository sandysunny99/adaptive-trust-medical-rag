# Live Provider Capability Matrix V3

## Capabilities

| Provider | Adapter | generate() | generate_structured() | JSON Schema Support |
|---|---|---|---|---|
| **Groq** | OpenAICompatibleBackend | ? PASS | ? PASS | Native |
| **NVIDIA** | OpenAICompatibleBackend | ? PASS | ? PASS | Native |
| **Cloudflare** | OpenAICompatibleBackend | ? PASS | ? PASS | Native |
| **Hugging Face** | OpenAICompatibleBackend | ? FAIL | ? FAIL | Unreliable |

## Conclusion
Cloudflare has been upgraded from a legacy adapter to the OpenAICompatibleBackend and verified to fully support complex nested JSON schema generation for the Answer Safety Gate.
