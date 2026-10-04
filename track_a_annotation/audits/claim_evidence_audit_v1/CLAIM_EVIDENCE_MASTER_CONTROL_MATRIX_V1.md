# MASTER CONTROL MATRIX

| Control | Specified | Implemented | Tested | Provenance | Fail Behavior | Validation Level | Finding |
|---|---|---|---|---|---|---|---|
| Claim Parsing | Yes | Yes | Yes | N/A | Excludes | UNIT | OK |
| Support Verification | Yes | Yes | Yes | N/A | Qualify/Abstain | UNIT | OK |
| Contradiction | Yes | Yes | Yes | N/A | Abstain | UNIT | OK |
| Citation Provenance | Yes | Yes | Yes | Broken | Ignores failure | UNIT | **PROVENANCE_GAP** |
| Trust Propagation | Yes | No | No | N/A | Blind | NONE | **TRUST_PROPAGATION_GAP** |
| Relationship Gating | Yes | Pre-Gen Only | Yes | N/A | Blind post-gen | NONE | **RELATIONSHIP_GAP** |
