# TRUST P0 POLICY DESIGN DECISION V1

- **CURRENT IMPLEMENTATION**: Available-factor renormalization.
- **EXISTING SPECIFICATION**: AGENTS.md mandates abstention when evidence is missing, particularly for R3 scenarios.
- **POLICY GAP**: The numerical translation of "missing evidence" into a scoring formula is not mathematically defined by the specs, though the *outcome* (abstention) is explicitly mandated.
- **SUPPORTED POLICY**: Required-Factor Abstention (Policy B) is most closely aligned with the existing rules.
- **UNSUPPORTED POLICY**: Available-factor renormalization (Policy A) conflicts directly with safety requirements.
- **DESIGN REQUIRED**: Yes. A formal specification update is needed to define exactly how `TrustFactorScores` communicates missing data to the orchestrator to guarantee abstention without relying on implicit float thresholds.
