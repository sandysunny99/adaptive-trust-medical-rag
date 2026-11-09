# Live LLM Provider Audit V3

## 1. Provider Class and Interface
- **Class:** `GroqBackend` (located in `src/adaptive_trust_medical_rag/llm_backend/groq_backend.py`)
- **Protocol:** Implements the `generate(prompt: str, response_format: dict[str, str] | None = None) -> ModelGenerationResult` signature for standard interaction, returning a `ModelGenerationResult` dataclass.

## 2. API Endpoint and Parameters
- **Endpoint:** `https://api.groq.com/openai/v1/chat/completions`
- **Timeout:** 30.0 seconds
- **Default Model:** `openai/gpt-oss-120b` (Can be overridden by config)
- **Temperature:** `0.0` (Hardcoded strictly to zero in `app.py` instantiation to minimize hallucinations).
- **Max Tokens:** Null by default, can be optionally set.

## 3. Streaming and Structured Output Support
- **Streaming:** Not currently implemented natively via `httpx.AsyncClient().stream`. The backend waits for the full text completion before returning.
- **Structured Output:** Added support for `response_format={"type": "json_object"}`. Passed in by the Orchestrator/Service to natively extract `json` payload. 

## 4. Error Handling and Failure Mapping
- **Exception Classes:** `ModelExecutionError`.
- **Handling:** Caught within `live_application.py`, logs the exact reason, and returns the explicit fail-safe `PROVIDER_FAILURE` SSE event. In the case where `GROQ_API_KEY` is completely missing from the environment, the `app.state.llm_backend` initializes to `None`, which causes the service to yield `PROVIDER_CONFIGURATION_REQUIRED` and immediately abort LLM generation without any fake/fallback data.
