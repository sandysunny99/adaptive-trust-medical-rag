# Live LLM Environment Matrix

## Environment State
- **File Checked:** `.env.local`
- **Groq Credentials:** Present (`GROQ_API_KEY=***`)
- **Nvidia Credentials:** Present (`NVIDIA_API_KEY=***`)
- **Gemini Credentials:** Present (`GEMINI_API_KEY=***`)
- **Primary LLM Provider:** Nvidia (configured via `LLM_PROVIDER` logic default)

## Execution Mode
When running the `test_v6_*.py` suite:
- `TESTING="1"` is exported by PyTest or CI.
- Rate limits in `app.py` are explicitly bypassed to prevent local and CI `HTTP 429` failures.
- Pytest hooks and test setups correctly inject mocked retrieval endpoints.
- However, since credentials are present, the live LLM integration code paths *will* execute their backend calls, effectively serving as an end-to-end integration validation against the live LLM provider for tests that aren't strictly mocked out.
