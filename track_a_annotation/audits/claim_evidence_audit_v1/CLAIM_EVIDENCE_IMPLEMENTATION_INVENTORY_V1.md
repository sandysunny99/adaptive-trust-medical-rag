# CLAIM EVIDENCE IMPLEMENTATION INVENTORY V1

| Component | File | Class/Function | Input | Output | Purpose | Tests | Validation Level |
|---|---|---|---|---|---|---|---|
| Atomic Claim Parsing | `claim_verifier_v2.py` | `decompose_into_claims` | `answer: str` | `list[AtomicClaim]` | Extract verifiable clauses and citations | `test_claim_verifier_v2.py` | UNIT_VALIDATED |
| Semantic Evaluation | `claim_verifier_v2.py` | `_evaluate_pair` | `premise: str`, `hypothesis: str` | `dict` (NLI scores) | Compute textual entailment | `test_claim_verifier_v2.py` | UNIT_VALIDATED |
| State Mapping | `claim_verifier_v2.py` | `_map_to_state` | NLI max scores, chunks | `FinalSupportState` | Map NLI scores to support states | `test_claim_verifier_v2.py` | UNIT_VALIDATED |
| Gate Decision | `claim_verifier_v2.py` | `verify` | `answer`, `list[EvidenceChunk]` | `VerificationReportV2` | Decide release/qualify/abstain | `test_claim_verifier_v2.py` | UNIT_VALIDATED |
| Orchestrator Integration | `rag_orchestrator.py` | `RAGOrchestrator.generate_answer` | `RAGRequest` | `RAGResponse` | Execute full pipeline | `test_provider_runtime_integration.py` | ADAPTER_LEVEL_VALIDATED |
