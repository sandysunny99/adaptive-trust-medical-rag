# TRIGGER MATRIX

| Trigger | Class | Implementation | Stage | State Output |
|---|---|---|---|---|
| Zero Evidence | NO_EVIDENCE | `MIN_ELIGIBLE_CHUNKS` | Pre-Gen | `abstained=True` |
| Low Trust | LOW_TRUST | `AdaptiveTrustScorer` | Pre-Gen | `abstained=True` (if all fail) |
| Unsupported Claim | UNSUPPORTED | `ClaimVerifierV2` | Post-Gen | `GateDecision.abstain` |
| Invalid Citation | INVALID_CITATION | `ClaimVerifierV2` | Post-Gen | `GateDecision.abstain` |
| Relationship Block | RG02_BLOCK | `ClaimVerifierV2` | Post-Gen | `GateDecision.abstain` |
| Contradictory Evidence | CONTRADICTION | `ClaimVerifierV2` | Post-Gen | `GateDecision.abstain` |
