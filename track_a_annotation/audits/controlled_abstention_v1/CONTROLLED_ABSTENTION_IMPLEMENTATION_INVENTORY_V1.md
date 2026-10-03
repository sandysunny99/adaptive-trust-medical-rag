# IMPLEMENTATION INVENTORY

| Component | File | Function/Class | Trigger | Result | Consumer | Tests | Validation Level |
|---|---|---|---|---|---|---|---|
| Pre-Gen Gate | `rag_orchestrator.py` | `EvidenceEligibilityGate.evaluate` | `< MIN_ELIGIBLE_CHUNKS` | `passed=False` | `AdaptiveTrustRAGOrchestrator` | Unit/Int | High |
| Post-Gen Gate | `claim_verifier_v2.py` | `AnswerSafetyGate.verify` | `unsupported_claims > threshold` | `GateDecision.abstain` | `AdaptiveTrustRAGOrchestrator` | Unit/Int | High |
| Trust Scorer | `trust_scorer.py` | `AdaptiveTrustScorer.score_batch` | `trust < risk_threshold` | Removes chunks | `EvidenceEligibilityGate` | Unit | High |
| Claim Verifier | `claim_verifier_v2.py` | `ClaimVerifierV2.verify` | `citation_supports=False` | `UNSUPPORTED` | `AnswerSafetyGate` | Unit | High |
