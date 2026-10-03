# TRUST P0 NONE DOWNSTREAM SAFETY AUDIT V1

The `trust_score` output by `AdaptiveTrustScorer` remains a strict `float`. Downstream consumers (e.g. `rag_orchestrator.py`, `live_variants.py`) compare `trust_score` mathematically against threshold values. Since `None` never escapes `trust_scorer.py` as the overall score, mathematical operations remain completely type-safe.
