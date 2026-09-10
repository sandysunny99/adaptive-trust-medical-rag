# V3.1 Pilot Scope Proposal

## Current Requirement
The frozen validation specification currently requires a completed decision for every single case-document pair.
For the 10-case pilot, this equates to exactly **2,480 row-level judgments**.

## Operational Bottleneck
Forcing a human reviewer to manually mark `NOT_RELEVANT` across thousands of topically-unrelated background documents is extremely expensive and causes annotator fatigue, degrading the quality of the positive-evidence review.

## Proposed Reduction
If the research protocol allows, we propose modifying the validator (`scripts/validate_v3_1_human_submission.py`) to accept a **Candidate Verification Mode**:
1. The human reviewer explicitly annotates the identified candidate documents and any newly discovered evidence.
2. The human explicitly approves a case-level closure (e.g. marking the remaining unannotated candidates as assumed `NOT_RELEVANT` implicitly, or explicitly via a script AFTER human sign-off).
3. The human may assign `NO_EVIDENCE` at the case level if they conclude the candidates and manual searches yielded no support.

## Decision Required
Until this proposal is formally approved and the validator is updated, Anti-Gravity will enforce the strict 2,480-row requirement. We await your explicit approval to implement this reduction.
