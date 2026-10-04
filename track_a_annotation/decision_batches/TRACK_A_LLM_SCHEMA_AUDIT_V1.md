# TRACK_A_LLM_SCHEMA_AUDIT_V1

## Separate Schema Hashes
The system now enforces separate semantic structures:
1. TRANSPORT_TEST_SCHEMA_SHA256: A temporary minimal schema for proving JSON capability and transport connectivity.
2. TRACK_A_ADJUDICATION_SCHEMA_SHA256: The full frozen schema enforcing query analysis, evidence analysis, claims, alignment, labels, grades, and exact span fields.

This prevents the temporary transport structure from being permanently recorded as the Track A protocol schema.
