# Technical Debt Register

**Date:** 2026-08-30  
**Commit:** 4a704f5  

---

## CRITICAL — Blocks Research Validity

| ID | Item | File | Impact |
|---|---|---|---|
| TD-001 | LiveModelAdapter generates a local template string instead of calling a real LLM | evaluation/live_variants.py L149 | ALL faithfulness, hallucination, and quality metrics are invalid |
| TD-002 | Variant B and C call identical retriever code with identical corpus; B!=C only in metadata flags | evaluation/live_variants.py L446-L584 | Ablation B-vs-C comparison is scientifically invalid |
| TD-003 | Evidence corpus has only 4 documents in base and 18 in F1; retrieval evaluation is not meaningful at this scale | data/evidence/manifest.json | Precision@K has no scientific meaning over 4 documents |
| TD-004 | SimpleEmbeddingModel uses 7 hardcoded vocabulary words; results called "dense retrieval" are binary word-presence matches | evaluation/live_variants.py L53-63 | Dense retrieval claims are not comparable to any published embedding baseline |

---

## HIGH — Should Fix Before Final Experiments

| ID | Item | File | Impact |
|---|---|---|---|
| TD-005 | Trust execution metadata in ablation logs reports hardcoded weights (0.35/0.30) inconsistent with trust.yaml (0.20/0.10) | evaluation/live_variants.py L751-756, L868-873 | Audit trail shows wrong weights; reproducibility claim weakened |
| TD-006 | All 7 metrics reported without multiple testing correction | evaluation/f0_f1_integrity.py, scripts/run_f0_f1_experiment.py | Inflated false-discovery rate |
| TD-007 | No primary outcome metric pre-registered | All experiment scripts | Introduces researcher degrees of freedom |
| TD-008 | Graph retrieval edges are manually hardcoded; no drug knowledge base | retrieval/hybrid_retrieval.py | Graph retrieval results not generalizable |
| TD-009 | No adversarial test cases in any evaluation dataset | tests/dev_dataset_v1.jsonl, tests/val_dataset_v1.jsonl | Security claims unquantified |

---

## MEDIUM — Should Fix Before Publication

| ID | Item | File | Impact |
|---|---|---|---|
| TD-010 | Literature review has 0 verifiable citations | reports/research/literature_review_2026.md | Cannot be submitted; must be rebuilt |
| TD-011 | Claim verifier is rule-based lexical overlap; will misclassify semantically equivalent claims | verification/claim_verifier.py | Inflated hallucination rate; understates actual system quality |
| TD-012 | Database models defined but no live PostgreSQL/pgvector connection in any experiment | database/models.py, database/session.py | Retrieval not production-equivalent |
| TD-013 | No sample size justification (power analysis) for 20-case experiments | All experiment manifests | Statistical section of paper weak |
| TD-014 | No abstention rate calibration (correct abstention vs false abstention vs unsafe non-abstention) | orchestrator/rag_orchestrator.py | Research Question RQ7 cannot be answered |

---

## LOW — Can Remain as Future Work

| ID | Item | File | Impact |
|---|---|---|---|
| TD-015 | No frontend web UI | api/ | Demonstration quality only; not required for paper |
| TD-016 | No real-time contradiction detection between retrieved sources | verification/claim_verifier.py | Contradiction detection is pattern-based only |
| TD-017 | No rate limiting implementation in P0 adapters | evidence_sources/ | Risk of API abuse if deployed; acceptable for research |
| TD-018 | Docker-compose.yml defines postgres but is not used in experiments | docker-compose.yml | Development friction only |
| TD-019 | RESULT_HASH_SPECIFICATION.md referenced in verifier but not confirmed in repo | docs/ | Documentation completeness |
