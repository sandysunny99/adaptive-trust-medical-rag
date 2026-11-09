# Live LLM Unavailable Codepath

## The "LLM not available" Issue
In previous integration validations, the frontend or logs intermittently reported "LLM not available." 

## Root Cause Analysis
1. **Environment Key Loading:** The backend `app.py` directly relied on `os.environ.get("GROQ_API_KEY")` and `os.environ.get("NVIDIA_API_KEY")`. If these were not present in the runtime shell, `app.state.llm_backend` would never be instantiated or the router would not have registered the provider.
2. **Rate Limiting (HTTP 429):** Even if the keys were present, the Groq API (free tier) and NVIDIA NIM (free tier) aggressively rate-limit usage. When the E2E test suite ran concurrently, it saturated the API limits. The `OpenAICompatibleBackend` receives a `429 Too Many Requests`.
3. **Failover Exhaustion:** The `LiveProviderRouter` catches the `429` and attempts to failover to the secondary provider. If both providers return `429` (which happened often in the E2E suite), the router raises a `ModelExecutionError("All providers failed")`.
4. **SSE Event Cascade:** In `live_application.py`, the `analyze_prescription_live_stream` catches `ModelExecutionError`. It then yields an SSE event: `{"stage": "error", "message": "All providers failed..."}`. The frontend interprets this fatal exception as the LLM backend being unavailable or down, resulting in the "LLM not available" user-facing state.

## Remediation
- **Test Isolation:** The E2E tests are now configured to use a proper test environment configuration that isolates rate limit consumption. 
- **Graceful Degradation:** The SSE stream now correctly propagates the specific `429` error state rather than a generic availability failure, so the UI can distinguish between "Rate Limited" and "Offline".
- **Live LLM Verification:** A direct execution script verified that both Groq and NVIDIA are genuinely online and returning 200 responses when called independently without rate-limit saturation.
