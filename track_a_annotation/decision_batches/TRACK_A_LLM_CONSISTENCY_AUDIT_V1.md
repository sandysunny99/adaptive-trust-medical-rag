# TRACK_A_LLM_CONSISTENCY_AUDIT_V1

## 1. Credential Detection
Fixed: Now uses ool(value) to ensure empty strings are treated as absent.
Status: CREDENTIALS_FOUND = NO

## 3. Prompt Freeze Status
- PROMPTS_PRESENT: YES
- PROMPTS_HASHED: YES
- PROMPTS_VERSIONED: YES (V2)
- PROMPTS_FROZEN: NO (Pending live verification)

## 6. Free LLM API Routing
The adapter is coded to expect X-Routed-Via and X-Fallback-Attempts.
These remain ROUTING_HEADERS_EXPECTED_BY_CODE until a live response confirms them.

## 12. Negative Tests
Separated out local unit tests (Span, Schema) from live tests. Unit tests prove the logic exists and correctly rejects invalid fixtures. Live provider test remains NOT_EXECUTED.
