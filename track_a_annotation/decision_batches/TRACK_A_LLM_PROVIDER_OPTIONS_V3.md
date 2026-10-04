# TRACK_A_LLM_PROVIDER_OPTIONS_V3

## Selection of Target Configurations
The final medical annotation run relies on the researcher picking a distinct and pinned infrastructure combination. **Do not run the pilot automatically.**

| Execution Mode | Expected Latency | Structured Output Method | Routing Predictability | Credential Required |
|---|---|---|---|---|
| DIRECT_GROQ | Low | JSON_OBJECT | High (Direct) | GROQ_API_KEY |
| DIRECT_CLOUDFLARE | Low | JSON_OBJECT | High (Direct) | CLOUDFLARE_API_KEY + ACCOUNT_ID |
| DIRECT_HUGGINGFACE | Medium | PROMPT_ONLY | High (Direct) | HUGGINGFACE_API_KEY |
| FREELLMAPI_GATEWAY | Varies | JSON_OBJECT | Variable (Tracked via Headers) | FREELLMAPI_API_KEY |
