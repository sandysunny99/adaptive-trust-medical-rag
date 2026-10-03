# TRUST ALL FACTORS MISSING POLICY MATRIX V1

| Factor | Required? | Missing Possible? | Safety Critical? | Current Missing Semantics | Specified Behavior | Policy Needed? |
|---|---|---|---|---|---|---|
| `source_authority` | Yes | Yes | Yes (MVA 0.3) | Denominator excluded | Must have verified high-authority | Yes |
| `query_relevance` | Yes | Yes | Yes | Denominator excluded | Missing evidence must abstain | Yes |
| `evidence_quality` | Optional/Context | Yes | Yes | Denominator excluded | Unknown | Yes |
| `freshness` | Optional | Yes | No | Denominator excluded | Unknown | Yes |
| `consistency` | Optional | Yes | Yes | Denominator excluded | Unresolved contradictions abstain | Yes |
| `entity_match` | Yes | Yes | Yes | Denominator excluded | Must accurately match RxCUI | Yes |
| `population_match` | Context | Yes | Yes | Denominator excluded | Constraints must be preserved | Yes |
| `anti_poisoning` | Yes | Yes | Yes | Denominator excluded | Quarantined if high | Yes |
| `anti_injection` | Yes | Yes | Yes | Denominator excluded | Must be escaped/stripped | Yes |
