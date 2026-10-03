# TRUST P0 FACTOR SAFETY POLICY MATRIX V2

| Factor | Required? | Safety Critical? | Missing Allowed? | Missing Effect | Source |
|---|---|---|---|---|---|
| `source_authority` | Yes | Yes | Yes (MVA 0.3) | Dilutes score, hard block | SPECIFIED |
| `query_relevance` | Yes | Yes | Yes | Dilutes score heavily | SPECIFIED |
| `evidence_quality` | Context | Yes | Yes | Dilutes score | UNSPECIFIED |
| `freshness` | Optional | No | Yes | Dilutes score | UNSPECIFIED |
| `consistency` | Optional | Yes | Yes | Dilutes score | SPECIFIED |
| `entity_match` | Yes | Yes | Yes | Dilutes score | SPECIFIED |
| `population_match` | Context | Yes | Yes | Dilutes score | SPECIFIED |
| `anti_poisoning` | Yes | Yes | Yes | Dilutes score, hard block | SPECIFIED |
| `anti_injection` | Yes | Yes | Yes | Dilutes score, hard block | SPECIFIED |
