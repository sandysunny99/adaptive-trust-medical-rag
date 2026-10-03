# FINAL OUTPUT MATRIX

| Condition | Detection Point | State | Generation Allowed? | Verification Allowed? | Final Output Allowed? | Abstain/Block? |
|---|---|---|---|---|---|---|
| No Evidence | EligibilityGate | `passed=False` | NO | NO | NO | ABSTAIN |
| All chunks low trust | EligibilityGate | `passed=False` | NO | NO | NO | ABSTAIN |
| Invalid Citation | ClaimVerifierV2 | `UNSUPPORTED` | YES | YES | NO (if Gate fails) | ABSTAIN |
| Unsupported Claim | ClaimVerifierV2 | `UNSUPPORTED` | YES | YES | NO (if Gate fails) | ABSTAIN |
| Contradiction | ClaimVerifierV2 | `CONTRADICTED` | YES | YES | NO | ABSTAIN |
