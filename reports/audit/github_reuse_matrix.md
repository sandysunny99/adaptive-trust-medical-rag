# GitHub & Module Reuse Decision Matrix

| Target Component | Source / Reference | Current Function | Reusable Action | Decision Rationale |
|------------------|--------------------|------------------|-----------------|--------------------|
| Input Sanitizer | Aegis Node / Internal | Prompt injection defense | ADAPT | Adapted regex & injection marker patterns for medical queries |
| Security Middleware | CloudShield / FastAPI | Rate limit & security headers | ADAPT | Adapted middleware stack for FastAPI lifespan app factory |
| Audit Logger | Internal / CloudShield | SHA-256 query telemetry | REUSE AS-IS | Reused SHA-256 hashing pattern to guarantee Zero PHI |
| Vector Search | pgvector | Vector similarity search | REUSE AS-IS | Native PostgreSQL extension reused via SQLAlchemy |
| SAST Tooling | Bandit + Semgrep | Static analysis & security rules | REUSE AS-IS | Configured `.bandit` INI and `.semgrep/medical-rag-security.yml` |
