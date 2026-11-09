> **WARNING: HISTORICAL / SUPERSEDED BY V3**
> This document is maintained for research provenance. For the current LIVE application provider status, refer to the V3 documents.

# Live SSE Validation

## Objective
Verify that Server-Sent Events (SSE) properly transmit provider states, failover states, and errors to the React frontend.

## Validation Scenarios

### 1. Success Streaming
- **Verification**: The `LiveProviderRouter` yields structured output dictionaries. The `LiveMedicalRAGService` wraps these into `pipeline_stage: generating` and `pipeline_stage: complete` SSE events. Verified in the E2E tests (`test_sse_isolation_and_security`).

### 2. Provider Error (All Failed)
- **Verification**: If `LiveProviderRouter` raises `ModelExecutionError` after exhausting all providers, the service catches it and emits a `pipeline_stage: error` event with the structured error class. Verified by `test_api_input_validation` testing the exception catching.

### 3. Failover Streaming
- **Verification**: The failover happens *inside* `LiveProviderRouter.generate_structured`. It is a synchronous await. The SSE stream simply waits slightly longer while the fallback occurs. The stream does not break, and the frontend receives the successful fallback payload seamlessly.

## Conclusion
The SSE pipeline securely wraps the multi-provider routing layer, translating internal provider status into appropriate client-side events.
