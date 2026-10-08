# Live Provider Routing V3

## Architecture
The Live Provider Router implements a strict infrastructure-level failover cascade that preserves medical safety guarantees.

`mermaid
graph TD
    A[Request] --> B{Groq (Primary)}
    B -- Success --> Z[Answer Safety Gate]
    B -- 429 / 504 / 503 --> C{NVIDIA (Secondary)}
    C -- Success --> Z
    C -- 429 / 504 / 503 --> D{Cloudflare (Tertiary)}
    D -- Success --> Z
    D -- 429 / 504 / 503 --> E[Final ModelExecutionError]
    
    B -- Medical Safety Error --> F[Propagate Error (No Failover)]
    C -- Medical Safety Error --> F
    D -- Medical Safety Error --> F
`

## Safety Enforcement
The fallback cascade is **ONLY** triggered by transport-layer failures (timeouts, network drops, HTTP 429/502/503/504). It never triggers if the LLM output is rejected by the Evidence Eligibility Gate or the Claim Verifier.
