# TRUST MISSING DATA POLICY GAP V1

**EXISTING RULE**: "When evidence is missing... the system must abstain using the standard structured abstention template." (AGENTS.md 2.4).
**EXISTING RULE**: "Query involves High-Risk (R3) scenarios... without verified high-authority evidence" must abstain.

**CURRENT IMPLEMENTATION**: Calculates trust score by excluding missing data from the denominator (`weight_sum`), mathematically normalizing the score over fewer factors.

**POLICY GAP**: The project specifications clearly demand safety-via-abstention when evidence is missing. The implementation incorrectly uses available-factor renormalization, inadvertently bypassing the hard safety gate. A formal policy mapping "which missing factors mathematically force abstention for which risk tiers" is required.
