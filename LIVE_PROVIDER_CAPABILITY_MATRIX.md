# Live Provider Capability Matrix

| Provider | Text | Streaming | Context | Auth | Rate Limit | Error Mapping | Live Compatible |
|---|---|---|---|---|---|---|---|
| Groq | Yes | Yes (via `OpenAICompatibleBackend`) | 8k+ | Standard Header | Native `429` parsing | Full `FailureClass` mapping | Yes |
| NVIDIA NIM | Yes | Yes (via `OpenAICompatibleBackend`) | 8k+ | Standard Header | Native `429` parsing | Full `FailureClass` mapping | Yes |
| Hugging Face | Yes | No (legacy adapter) | Variable | Bearer Token | Minimal | `ModelExecutionError` basic | No (lacks `generate_structured`) |
| Cloudflare AI | Yes | No (legacy adapter) | Variable | Bearer Token | Minimal | `ModelExecutionError` basic | No (lacks `generate_structured`) |
| FreeLLM API | Yes | No (via `PilotAdapter`) | Variable | Header | Minimal | `ModelExecutionError` basic | No (lacks `generate_structured`) |

### Context Limits
*Context limits depend on the exact selected model endpoint. Groq and NVIDIA endpoints natively support structural parsing required by the medical evidence gates.*
