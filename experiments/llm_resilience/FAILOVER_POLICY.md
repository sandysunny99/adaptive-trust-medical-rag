# Failover Policy

## Failover-Eligible Failure Classes

| Failure Class | Failover? | Retry? | Example |
|---|---|---|---|
| RATE_LIMIT | YES | YES | 429 Too Many Requests |
| TRANSIENT_PROVIDER | YES | YES | 502, 503 |
| TIMEOUT | YES | YES | Request timeout, 504 |
| CAPACITY | YES | YES | Provider overload |
| NETWORK | YES | YES | Connection error, DNS failure |
| AUTHENTICATION | NO | NO | 401 Unauthorized |
| AUTHORIZATION | NO | NO | 403 Forbidden |
| INVALID_REQUEST | NO | NO | 400 Bad Request |
| MODEL_NOT_FOUND | NO | NO | Invalid model ID |
| SCHEMA_ERROR | NO | NO | Structured output failure |
| APPLICATION_SEMANTIC | NO | NO | Security BLOCK, authorization denial |
| UNKNOWN | NO | NO | Unclassified error |

## Failover Flow

1. Primary provider receives the request
2. On transient failure: retry with exponential backoff + jitter
3. After retry exhaustion: evaluate circuit breaker
4. If failover enabled: route to next priority provider
5. Repeat retry cycle for secondary provider
6. If all providers exhausted: `AllProvidersUnavailableError` → controlled abstention

## Critical Rule

**Semantic failures MUST NEVER trigger failover.**

If Gemini produces an unsafe answer that the ClaimVerifier rejects, the router MUST NOT send the same request to Groq hoping for a different answer. That would be a security bypass.
