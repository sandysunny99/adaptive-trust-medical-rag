# TRUST MISSING DATA ABSTENTION INTERACTION V1

Controlled abstention is triggered by:
1. Trust score < threshold.
2. Source authority < 0.3.
3. Unsupported relationship grounding.
4. Answer safety gate failure (post-generation).

Currently, **MISSING EVIDENCE** (if translated to explicit `None`) skips the denominator. This allows the trust score to float above the threshold. As a result, the missing evidence fails to trigger abstention, collapsing the distinction between "Highly trusted evidence" and "Incomplete evidence that happened to score highly on the few metrics it had."
