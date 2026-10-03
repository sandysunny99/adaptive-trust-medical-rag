# TRUST P0 ALL-FACTOR REMEDIATION MATRIX V1

| Factor | Type | Default | Missing Representation | None Valid? | Scores? | Downstream Consumer | Regression Required? |
|---|---|---|---|---|---|---|---|
| `source_authority` | `float \| None` | `None` | `None` | Yes | Excluded | Scorer | Yes |
| `query_relevance` | `float \| None` | `None` | `None` | Yes | Excluded | Scorer | Yes |
| `evidence_quality` | `float \| None` | `None` | `None` | Yes | Excluded | Scorer | Yes |
| `freshness` | `float \| None` | `None` | `None` | Yes | Excluded | Scorer | Yes |
| `consistency` | `float \| None` | `None` | `None` | Yes | Excluded | Scorer | Yes |
| `entity_match` | `float \| None` | `None` | `None` | Yes | Excluded | Scorer | Yes |
| `population_match` | `float \| None` | `None` | `None` | Yes | Excluded | Scorer | Yes |
| `anti_poisoning` | `float \| None` | `None` | `None` | Yes | Excluded | Scorer | Yes |
| `anti_injection` | `float \| None` | `None` | `None` | Yes | Excluded | Scorer | Yes |
