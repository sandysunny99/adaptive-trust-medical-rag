# Threat Model & Security Specification

## 1. System Boundaries & Untrusted Inputs

All incoming user queries and external document sources are treated as untrusted data inputs:
- User queries may contain prompt injection payloads, encoded instructions, or PHI.
- External documents may contain retrieval poisoning, outdated pharmacological claims, or misattributed entity assertions.

## 2. Threat Matrix & Countermeasures

| Threat ID | Threat Category | Description | Primary Defense | Enforcement Module |
|-----------|-----------------|-------------|-----------------|--------------------|
| **TM-01** | Direct Injection | Adversarial prompt override in query | Input Sanitizer | `security/sanitizer.py` |
| **TM-02** | Indirect Injection | Injected instructions in retrieved chunks | Prompt Isolation | `orchestrator/rag_orchestrator.py` |
| **TM-03** | Retrieval Poisoning | Malicious document placed in vector index | SHA-256 Ingestion Gate | `ingestion/evidence_ingester.py` |
| **TM-04** | PHI Leakage | Query containing patient identity data | PHI Scrubber & Hashing | `security/sanitizer.py`, `audit_logger.py` |
| **TM-05** | Hallucination | Fabricated contraindications or PMIDs | Dual Safety Gates | `claim_verifier.py`, `rag_orchestrator.py` |
