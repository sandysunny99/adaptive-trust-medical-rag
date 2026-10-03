# TRUST MISSING DATA POLICY OPTIONS V1

**Policy A: AVAILABLE-FACTOR RENORMALIZATION**
Missing factors excluded from numerator and denominator (Current Remediation).
- Source support: None specified.
- Architectural compatibility: High (maintains `float` trust_score).
- Safety semantics: Dangerously weak (allows highly incomplete evidence to pass strict gates).
- Mathematical implications: Score represents the average of *available* data, destroying absolute confidence signaling.

**Policy B: REQUIRED-FACTOR ABSTENTION**
If a safety-critical factor required for the current query/evidence context is missing, do not produce a normal trust decision and route to controlled abstention.
- Source support: Strongly aligned with AGENTS.md rule 2.4.
- Architectural compatibility: Requires updating `AdaptiveTrustScorer` or `rag_orchestrator` to treat missing critical factors as an automatic 0.0 or explicit `is_eligible=False`.
- Safety semantics: High safety. 

**Policy C: MINIMUM-AVAILABILITY REQUIREMENT**
Require a defined minimum proportion (e.g. > 50% of weights) or set of trust factors before scoring.
- Source support: Not explicitly defined in specifications.
- Architectural compatibility: Easy to implement in `AdaptiveTrustScorer`.

**Policy D: UNCERTAINTY-AWARE SCORE**
Produce a score plus an explicit completeness/uncertainty state, with separate gate logic.
- Source support: Aligns with conceptual framework, but no gate logic currently consumes a completeness state.
- Architectural compatibility: Requires modifications to the orchestrator to consume `missing_factors`.
