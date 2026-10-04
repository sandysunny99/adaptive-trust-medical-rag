# TRACK_A_LLM_PROVIDER_OPTIONS_V2

## Available Execution Modes
The system currently supports the following modes. No single mode is defined as the "best"; explicit configuration by the researcher is required to initiate the pilot.

| Execution Mode | Expected Latency | Structured JSON | Context Limitations | Reproducibility Risk |
|---|---|---|---|---|
| DIRECT_GROQ | Fast | Native JSON Schema | Depends on model | Low |
| DIRECT_CLOUDFLARE | Fast | JSON Mode | Depends on model | Low |
| DIRECT_HUGGINGFACE | Medium | Prompt + Syntax | Often limited to 4k-8k | Low |
| FREELLMAPI_GATEWAY | Varies | OpenAI Compatible | Depends on routed model | High (if automatic fallback triggers without tracking) |

*The researcher must select the target mode in config prior to pilot.*
