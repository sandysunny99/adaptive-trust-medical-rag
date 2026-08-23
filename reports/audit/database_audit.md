# Database Schema & Alembic Migration Audit

## Schema Table Inventory

| Table Name | Primary Key | Key Columns | Indexes | Security / Integrity Properties |
|------------|-------------|-------------|---------|----------------------------------|
| `evidence_sources` | UUID (`gen_random_uuid()`) | `name`, `authority_tier`, `reputation_score` | Index on `authority_tier` | Source authority validation |
| `documents` | UUID (`gen_random_uuid()`) | `source_id`, `sha256_hash`, `validation_status` | Unique on `sha256_hash` | SHA-256 provenance & quarantine |
| `evidence_chunks` | UUID (`gen_random_uuid()`) | `document_id`, `chunk_text`, `embedding` | IVFFlat index on `embedding VECTOR(768)` | Fast vector similarity search |
| `evidence_provenance` | UUID (`gen_random_uuid()`) | `chunk_id`, `provenance_metadata` | Index on `chunk_id` | Audit trail of ingestion |
| `audit_events` | UUID (`gen_random_uuid()`) | `query_hash`, `risk_tier`, `gate_decision` | Index on `query_hash` | Zero PHI (query hash only) |

## Migration Chain Status
- Initial revision: `0001_initial`
- Migration chain status: **VERIFIED & CLEAN** (No gaps, no cycles)
