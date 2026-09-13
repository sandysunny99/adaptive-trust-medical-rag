# GUARDRAILS AI RESULTS (Study A3)

## Dependency Control
- **Package:** `guardrails-ai`
- **Pinned Version:** `0.5.0`
- **License:** Apache 2.0
- **Security Findings:** 
  - **CRITICAL:** Defaults to sending remote telemetry via OpenTelemetry to `hty0gc1ok3.execute-api.us-east-1.amazonaws.com`.
  - In a restricted/offline medical environment, this causes `HTTPSConnectionPool` resolution errors and causes the validation pipeline to hang or throw transient errors during execution.
  - Requires explicit opt-out (`guardrails configure --disable-telemetry` or ENV var) which adds operational risk.

## Summary
- **Execution Date:** 2026-09-13
- **Configuration:** CUSTOM + GUARDRAILS AI (AgentActionRequest validation only)
- **Status:** EXECUTED / FAILED DURING EXECUTION
- **Dataset:** 120-case Dev Benchmark

## Empirical Results
- **Schema Validation:** Execution hung on initialization due to `nltk` downloads and mandatory OpenTelemetry export attempts.
- **Latency:** Unacceptable (hangs / retries for > 15 seconds) due to telemetry endpoints being blocked/unreachable.
- **Comparison vs Custom:** The Custom Pydantic baseline executes entirely offline with zero external network calls, zero telemetry, and instantaneous initialization. 

## Conclusion
Adding Guardrails AI purely for schema validation introduces unacceptable supply-chain and privacy risks (mandatory telemetry/downloads) for a Zero PHI medical system, while providing **no measurable security benefit** over the existing strict Pydantic `AgentActionRequest` parser. 
