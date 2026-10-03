# TRUST P0 POST-REMEDIATION CALLSITE AUDIT V1

- **rag_orchestrator.py:502**: Omits `query_relevance`, `evidence_quality`, and `population_match`. These correctly resolve to `None`. No hidden default injection.
- **live_variants.py:661**: Omits `evidence_quality`, `freshness`, `population_match`, `consistency`, `anti_poisoning`, `anti_injection`. Resolves to `None`. No hidden defaults.
