# Security Control Matrix

| Threat Category | Pre-Retrieval Control | Retrieval Control | Context Control | Generation Control | Post-Generation Control |
|-----------------|----------------------|-------------------|-----------------|--------------------+-------------------------|
| **Direct Prompt Injection** | Input Sanitizer | N/A | Prompt Isolation Template | Grounded Generation Framing | N/A |
| **Indirect Retrieval Injection** | N/A | Source Authority Gating | Data-only Context Formatting | System Directive Override Guard | Answer Safety Gate |
| **Retrieval Poisoning** | Ingestion Quarantine | SHA-256 Provenance Check | Trust Threshold Re-Ranking | Strict Citation Gating | Controlled Abstention |
| **PHI / PII Leakage** | PHI Pattern Detection | N/A | Query Hash Logging (`query_hash`) | Telemetry Scrubbing | Audit Log Redaction |
| **Hallucinated PMIDs/URLs** | N/A | N/A | Context Citation Mapping | Strict PMID Matching | Answer Safety Gate Verification |
