# TRUST MISSING DATA MATRIX V1
| Field | Present | Missing | Default | Imputed | Explicit Unknown | Downstream Effect |
|---|---|---|---|---|---|---|
| query_relevance | float | silently defaults | 0.0 | No | No | Artificially fails trust gate |
| evidence_quality | float | silently defaults | 0.0 | No | No | Artificially fails trust gate |
| population_match | float | silently defaults | 1.0 | No | No | Artificially inflates trust |
| freshness | float | silently defaults | 1.0 | No | No | Artificially inflates trust |
**Conclusion**: The dataclass `TrustFactorScores` assigns silent defaults (0.0 or 1.0). Missing data is treated exactly as zero evidence or perfect evidence, bypassing explicit missing-data safety checks.
