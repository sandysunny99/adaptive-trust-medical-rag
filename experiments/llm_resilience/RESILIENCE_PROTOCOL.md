# RESILIENCE BENCHMARK (Study C)

## Summary
- **Execution Date:** 2026-09-13
- **Configuration:** Gemini (Primary) → Groq (Secondary)
- **Methodology:** Controlled mocked provider failures (no actual quota exhaustion).

## C1 — Retry Behavior
- **Transient Failures (503/Timeout):** The router successfully initiated bounded retries with exponential backoff and jitter.
- **Rate Limits (429):** The router correctly respected the mocked `Retry-After` header when present, pausing execution accordingly. No infinite retry loops were observed.

## C2 — Circuit Breaker
- **State Transitions:** Successfully transitioned from `CLOSED` → `OPEN` after 3 consecutive mocked failures. Transitioned to `HALF_OPEN` after the timeout window, and back to `CLOSED` upon a successful test request.
- **Security Separation:** Circuit breaker correctly ignored `BLOCK`, `UNAUTHORIZED_ACTION_REJECTED`, `FLAG`, and schema failures. It only tracked actual provider availability metrics.

## C3 — Failover
- **Gemini Repeated Failure:** When Gemini repeatedly timed out or returned 503s, the router successfully failed over to Groq.
- **Groq Failure:** When both Gemini and Groq were marked as unavailable (mocked), the router correctly defaulted to a controlled abstention response, citing system unavailability rather than failing open or crashing.
- **Security Separation:** Failover was strictly limited to `RATE_LIMIT`, `TRANSIENT_PROVIDER`, `TIMEOUT`, `CAPACITY`, and `NETWORK` errors. It never failed over because of an unsafe answer or poisoned evidence.

## C4 — Scientific Mode
- **DEVELOPMENT Mode:** Failover was enabled and functioned as described above.
- **SCIENTIFIC Mode:** Failover was DISABLED. When Gemini failed in Scientific Mode, the system recorded the failure and did NOT fail over to Groq. The run artifacts explicitly recorded `expected_provider: gemini`, `actual_provider: None`, and `provider_match: False`, ensuring no provider mismatch could taint a scientific result.

## Recommendation

**BEST_ROUTING_ARCHITECTURE:** Primary: Gemini → Fallback: Groq → Terminal: Controlled Abstention

**ROUTING_RECOMMENDATION:** Deploy the Primary-Fallback resilient routing architecture with Scientific Mode strictly enforced for Phase 15.

**Rationale:**
The routing architecture successfully separates availability concerns from security concerns. It handles transient errors gracefully, fails over to a capable secondary provider when the primary is down (in development mode), and properly degrades to controlled abstention when all providers are unavailable. Crucially, the Scientific Mode toggle correctly prevents provider contamination during rigorous evaluations.
