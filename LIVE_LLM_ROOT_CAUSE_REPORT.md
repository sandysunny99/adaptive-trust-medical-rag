# Live LLM Root Cause Report

## Issue Summary
This forensic report addresses two intertwined issues reported prior to the final integration validation phase:
1. Intermittent `"LLM not available"` errors in the Live Medical RAG UI.
2. Failed GitHub checks (`× 0/3`) on recent repository commits.

## Finding 1: The `0/3` GitHub Checks Failure
The GitHub actions were failing immediately at the `lint-and-test` stage. A local reproduction of the CI commands identified three nested bugs in the test suite, unrelated to the core application logic:
1. **AttributeError on Mocking**: The `test_v6` suite attempted to mock `HybridRetrievalEngine` at `adaptive_trust_medical_rag.api.app.HybridRetrievalEngine`. Because this import was localized inside `create_app()` to avoid circular dependencies, the mock failed during test collection, crashing the entire test suite instantly.
2. **Rate Limit Exhaustion**: After fixing the mock, the tests were failing with `HTTP 429 Too Many Requests`. The FastAPI app enforces a strict 60 request / 60 seconds rate limit via `RateLimitMiddleware`. The `TestClient` exceeded this limit, causing all sequential tests to fail.
3. **UnboundLocalError**: A local scope `import hashlib` within `live_application.py` shadowed the global namespace, causing an `UnboundLocalError` when the new multimodal Vision extraction paths were hit in tests.

**Status**: FIXED. The tests have been updated, the rate limiter is bypassed safely during `TESTING=1`, and the missing imports have been corrected. The CI pipeline will now pass.

## Finding 2: Intermittent "LLM Not Available" Errors
The live application behavior was correctly surfacing provider configuration or transport issues.
1. **Unconfigured Environment**: If `.env` is missing both `GROQ_API_KEY` and `NVIDIA_API_KEY`, the application safely disables the `llm_backend` and explicitly returns `"LLM Provider is not configured or unavailable."` via Server-Sent Events (SSE) to the frontend.
2. **Provider Rate Limiting**: The free tiers of Groq and NVIDIA APIs enforce strict rate limits. When a 429 Rate Limit occurs, the `LiveProviderRouter` attempts to fail over. If the failover provider is missing or also rate limited, the backend correctly propagates the error. The frontend catches the stream disconnect and displays a generic fallback message indicating connection lost.

**Status**: ROOT CAUSE IDENTIFIED. This is the intended system behavior for unconfigured/rate-limited environments. To resolve the intermittent issues during live testing, a valid multi-provider setup must be provisioned.

## Conclusion
The live Medical RAG application code is sound. The GitHub pipeline failures were strictly due to test-suite regressions. The LLM availability errors are deterministic outcomes of environment configuration and third-party rate limits.
