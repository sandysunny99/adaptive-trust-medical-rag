# CLAIM_EVIDENCE_REPRODUCIBILITY_CONTRACT_V1

## Component Evaluation Identity
The Claim-Evidence Component Verification must be strictly reproducible. As this module does not invoke an LLM for the verification logic (it uses heuristic overlap and regex), it is expected to be 100% deterministic.

- **Component version:** `claim_verifier.py` (Current frozen project state)
- **Test Matrix:** `CLAIM_EVIDENCE_TEST_MATRIX_V1.json`

## Evaluation Requirements
To pass the reproducibility contract:
1. Every run must map the identical `AtomicClaim` structure.
2. The `alignment_score` float must match exactly between runs.
3. The `GateDecision` (`release`, `qualify`, `abstain`) must remain identical.
4. The extraction of drug entities and citation IDs must yield the exact same array structure.

Any stochastic variance (e.g., set ordering differences leading to different `best_chunk_id` ties) must be documented.
