# FastAPI HTTP Layer Audit

| Route | HTTP Method | Request Schema | Response Schema | Middleware Active | Rate Limit | Test Status |
|-------|-------------|----------------|-----------------|-------------------|------------|-------------|
| `/query` | POST | `QueryRequest` | `QueryResponse` | RequestID, SecurityHeaders, RateLimit | 60 req / 60s | PASSED |
| `/ingest` | POST | `IngestRequest` | `IngestResponse` | RequestID, SecurityHeaders, RateLimit | 60 req / 60s | PASSED |
| `/health` | GET | None | `HealthResponse` | RequestID, SecurityHeaders | Exempt | PASSED |
| `/audit` | GET | None | `AuditResponse` | RequestID, SecurityHeaders, RateLimit | 60 req / 60s | PASSED |

**Security Headers Enforced:**
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
