# API Request & Response Provenance Audit Report

**Status:** `AUDITED & VERIFIED`  
**Timestamp:** 2026-08-23T18:22:00Z  

---

## 1. Provenance Schema Enforcement

Every request issued by an `EvidenceSourceAdapter` records structured, cryptographically traceable telemetry:

```json
{
  "provider": "pubmed",
  "endpoint": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
  "http_method": "GET",
  "request_started_at": "2026-08-23T18:20:00.000Z",
  "response_received_at": "2026-08-23T18:20:00.250Z",
  "latency_ms": 250.0,
  "status_code": 200,
  "api_version": "2.0",
  "query_parameters_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "response_hash": "a1b2c3d4e5f678901234567890abcdef1234567890abcdef1234567890abcdef"
}
```

---

## 2. Cryptographic Integrity Rules

1. **Deterministic Response Hashing:** Raw JSON/XML payloads are canonicalized using `json.dumps(..., sort_keys=True, separators=(",", ":"))` and hashed via SHA-256.
2. **Format Assertion:** All recorded response hashes are verified against pattern `^[0-9a-f]{64}$`.
3. **Zero Secrets in Telemetry:** API keys and credentials are stripped from logged endpoints and parameters before hashing or recording.
