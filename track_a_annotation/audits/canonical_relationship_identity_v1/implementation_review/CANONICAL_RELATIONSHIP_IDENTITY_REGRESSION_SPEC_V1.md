# Canonical Relationship Identity Regression Specification V1

## 1. Regression Contract
Implementation of Canonical Relationship Identity must not alter or break the existing verified semantics of previous research phases.

## 2. Preserved Boundaries
- **Trust P0 V2**: Trust dilution and full denominators must remain active. Canonical Identity acts after evidence chunking and does not alter the Trust Scorer's mathematical logic.
- **Claim-Evidence Remediation V1**: The post-generation safety verification of citations and claims remains active. The canonical check is strictly additive.
- **Controlled Abstention V1**: The formatting and routing of abstention logic must not be modified. Canonical failure merely feeds an `UNSUPPORTED` state into the existing gate.
- **RG-02 Semantics**: `NO_RELEVANT_RELATION` and status propagation must continue exactly as currently implemented. 
- **Track A & Retrieval**: No retrieval reruns or modifications to the benchmark dataset are permitted.

## 3. Required Regression Test Scenarios
1. `existing supported claim`: Must pass both NLI and Canonical Check.
2. `unsupported claim`: Must continue to fail.
3. `invalid citation`: Must continue to fail.
4. `NO_RELEVANT_RELATION`: Must trigger pre-generation or post-generation block.
5. `contradictory evidence`: Must trigger Abstention.
6. `mixed claims`: Valid claims pass while invalid claims are stripped.
7. `trust failure`: Low trust fails pre-generation gate regardless of identity match.
