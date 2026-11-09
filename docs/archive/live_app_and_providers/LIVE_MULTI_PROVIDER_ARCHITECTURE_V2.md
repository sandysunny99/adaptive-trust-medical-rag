> **WARNING: HISTORICAL / SUPERSEDED BY V3**
> This document is maintained for research provenance. For the current LIVE application provider status, refer to the V3 documents.

# Live Multi-Provider Architecture

## Overview
To improve live application resilience and decrease "LLM Unavailable" downtime caused by free-tier HTTP 429 Rate Limits, the application employs a multi-provider fallback strategy.

### Important Distinction: Token Quotas Are NOT Combined
Provider quotas do **NOT** become one shared token pool.
For example, having Groq, NVIDIA, and Hugging Face does **NOT** equal one giant LLM quota.
Instead, the architecture functions as a serial availability pool:
1. `Provider A` fails due to a network/transport error (e.g. Rate Limit).
2. `LiveProviderRouter` detects an *eligible* failure.
3. The router falls back to `Provider B`.

## Provider Priority
The priority is dynamically configured at startup. If a `LLM_PROVIDER` is specified in the environment, it is placed at the front of the queue. Configured providers are evaluated in this order:
1. NVIDIA NIM (Default Primary)
2. Groq (Secondary)
3. Hugging Face (Tertiary - Currently not integrated for structured generation)
4. Cloudflare AI (Quaternary - Currently not integrated for structured generation)
5. FreeLLM API (Not configured)

## Failure Classes and Failover Policy
Failover is explicitly **bounded to infrastructure errors**. The router will ONLY attempt the next provider if the exception maps to one of the following `FailureClass` categories:
- `RATE_LIMIT` (e.g., HTTP 429)
- `TIMEOUT`
- `TRANSIENT_PROVIDER` (e.g., HTTP 503)
- `NETWORK`
- `AUTHENTICATION` (if credentials suddenly rotate or expire)

### Important Medical Safety Requirement
**Provider failover must NOT bypass the medical evidence-control layer.**
If an LLM response is rejected because of a medical safety rule (e.g., `TRUST_FAILURE`, `CONTROLLED_ABSTENTION`, `RELATIONSHIP_MISMATCH`), the application **must not** retry on a different provider. These are safety outcomes based on the evidence, not provider transport failures.

## Retry Policy
For the live application, the router executes:
1. `Provider A` → Small bounded internal transport retry (if applicable) → Fails with `RATE_LIMIT`.
2. Router catches eligible transport failure.
3. `Provider B` → Small bounded internal transport retry → Returns `200 OK`.
*The V1.3 research runner logic remains entirely isolated and uses its own retry mechanics.*

## Provider Health States
The frontend receives clear telemetry regarding the status of the connection.
- `CONFIGURED`: The application loaded credentials for the provider.
- `HEALTHY`: The provider successfully returned a completion.
- `RATE_LIMITED`: The provider rejected the request due to quota saturation.
- `UNAVAILABLE`: The provider timed out or returned a 500 series error.
- `AUTH_FAILED`: The API key was rejected.

If all configured providers exhaust their attempts, a final `ModelExecutionError("No providers available")` is raised, bubbling up to the Server-Sent Events (SSE) stream as a structured provider error event, rather than generic application death.

## Security Boundaries
- Environment files (`.env`, `.env.local`) contain the exact API keys. These are git-ignored and never committed.
- The Frontend NEVER receives provider keys. The React application calls the FastAPI backend, which handles all provider authentication securely on the server-side.
