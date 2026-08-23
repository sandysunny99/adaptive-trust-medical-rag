# Research Alignment & Problem-Solution Matrix

| Literature Problem | Proposed Design | Implemented Module | Experiment / Verification | Status |
|--------------------+-----------------+--------------------+---------------------------|--------|
| Hallucinated Dosing / Contraindications | Post-Gen Answer Safety Gate | `claim_verification/claim_verifier.py` | Claim verification benchmark | VERIFIED |
| Stale Medical Evidence | Freshness Decay Scoring ($S_{fresh}$) | `source_validation/source_validator.py` | Trust scoring property tests | VERIFIED |
| Prompt Injection Overrides | Input Sanitizer & Prompt Isolation | `security/sanitizer.py` | Prompt injection attack matrix | VERIFIED |
| Retrieval Poisoning | SHA-256 Provenance & Authority Tiering | `ingestion/evidence_ingester.py` | Retrieval poisoning benchmark | VERIFIED |
| Source Authority Confusion | Multi-Factor Trust Scoring | `trust_scoring/trust_scorer.py` | Pre-Gen Eligibility Gate tests | VERIFIED |
| Overconfident Hallucinations | Risk Tier Controlled Abstention | `orchestrator/rag_orchestrator.py` | Abstention F1-score evaluation | VERIFIED |
