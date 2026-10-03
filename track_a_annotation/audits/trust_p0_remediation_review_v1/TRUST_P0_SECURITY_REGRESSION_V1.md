# TRUST P0 SECURITY REGRESSION V1

Relationship Grounding behavior (RG-02) relies on completely separate hard gate checks before/after trust scoring. The exclusion of missing dimensions in `TrustFactorScores` does not bypass `NO_RELEVANT_RELATION` checks in the orchestrator pipeline.
