# CONTROLLED ABSTENTION V1 - AUDIT REPORT

## Objective
Determine whether the current RAG architecture safely abstains or fails closed when evidence-control conditions are not satisfied.

## Scope
Audited pre-generation `EvidenceEligibilityGate` and post-generation `AnswerSafetyGate` in `rag_orchestrator.py` and `claim_verifier_v2.py`.

## Key Discoveries
1. **Zero Evidence Handling**: If 0 retrieved chunks pass the trust threshold, `EvidenceEligibilityGate` fails, and the system hard-blocks generation via `_abstain()`.
2. **Missing Trust**: Trust metadata properly reaches the `AnswerSafetyGate`. Missing R3 required factors trigger an abstention.
3. **Invalid Citation**: A generated claim citing an unrelated source triggers `UNSUPPORTED`. If any critical claims are unsupported, the post-generation gate issues `GateDecision.abstain`.
4. **Unsupported Relationship**: RG-02 status of `NO_RELEVANT_RELATION` blocks the claim via `UNSUPPORTED` state.
5. **Partial Abstention (Mixed Claims)**: Currently, if *some* claims are unsupported, the `AnswerSafetyGate` evaluates the proportion. If it falls below the confidence threshold, the *entire answer* is abstained. It does not surgically remove claims from the text.

## Conclusion
ABSTENTION CONTROL IS SUFFICIENTLY IMPLEMENTED FOR TESTED CONDITIONS.
