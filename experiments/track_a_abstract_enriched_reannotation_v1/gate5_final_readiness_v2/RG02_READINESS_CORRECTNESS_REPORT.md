# RG-02 Readiness Correctness Report

This report documents the semantic correctness audit of the RG-02 negative control case during the Final Gate 5 Readiness Validation.

## Phase 1 - Do Not Trust the Readiness Label
The previous readiness validation reported `GATE5_FINAL_READINESS_PASS` because the infrastructure completed successfully. However, the result for the negative control case RG-02 ("Statin is a drug. Cyanide is a poison.") was a `released` state. The audit below demonstrates that this was a semantic failure.

## Phase 2 - Recover the Authoritative RG-02 Definition
- **Case ID**: RG-02 (Negative Control)
- **Protocol**: Multi-entity queries require relationship-aligned evidence. Unrelated supported evidence must result in an `ENTITY_PAIR_MISMATCH` and prevent query release.
- **Expected Outcome**: `BLOCK` (`NO_QUERY_ALIGNED_SUPPORTING_EVIDENCE`).

## Phase 3 - Inspect the Actual RG-02 Runtime Trace
The `SECURITY_FINAL_READINESS_TRACE.jsonl` contains the exact record:
- **Case**: RG-02
- **Candidates Retrieved**: `chunk-spironolactone-001`, `chunk-metformin-001`, `chunk-warfarin-001`, `chunk-haloperidol-001`.
- **Grounding State**: `SUPPORTED`
- **Trust Scores**: ~0.58
- **Eligibility**: Passed
- **Decision**: `release`

## Phase 4 - Prove What Made RG-02 "SUPPORTED"
The `experiments/gate5_readiness_v1.py` script imported `RelationshipGroundingValidator` from the `v1` module (`relationship_grounding.py`), **not** `relationship_grounding_v2.py`.
The V1 validator evaluates candidates solely against their origin document in the registry. It verifies that the candidate's relationships are authentic to the source text. However, it **does not take the query as an argument**. Therefore, it never verifies whether the candidate's supported relationship matches the query's requested relationship. 

## Phase 5 - Entity Pair Alignment
The query endpoints are **Statin** and **Cyanide**. 
The candidates contained pairs like **Warfarin-Aspirin** or **Haloperidol-Azithromycin**.
Because the query-level alignment was bypassed, the `ENTITY_PAIR_MISMATCH` decision (which is correctly implemented in the V2 validator) was never reached.

## Phase 6 - Aggregate Release Logic
The `EvidenceEligibilityGate` in the orchestrator aggregated the `SUPPORTED` candidates, evaluated their trust scores against the R1 threshold (0.45), and correctly concluded that 4 candidates were eligible according to the data it received. The failure occurred upstream in the grounding module's instantiation. An unrelated supported candidate upgraded the aggregate query to `RELEASE`.

## Phase 7 - POS-02 Contamination Check
For POS-02 ("Does statin interact with aspirin?"):
- The returned candidates included `chunk-warfarin-001` (Warfarin and Aspirin) and `chunk-metformin-001`.
- None of the candidates contained the endpoint `statin`.
- This represents **Retrieval Contamination** (broad semantic similarity without exact entity match).
- Because the V1 validator was used, it returned `SUPPORTED` for these candidates, leading to an incorrect `release` decision for POS-02 on unrelated evidence.

## Phase 8 - Cognee vs Baseline Comparison
Both Cognee (25 candidates) and the Baseline (4 candidates) successfully retrieved chunks. The error was entirely downstream in the semantic evaluation layer (the V1 Grounding Validator).

## Phase 9 - Harness Inspection
The readiness harness (`experiments/gate5_readiness_v1.py`):
- Imported `RelationshipGroundingValidator` from `adaptive_trust_medical_rag.security_extensions.relationship_grounding` instead of `relationship_grounding_v2`.
- Called `grounding_val.validate(cand)` which takes only 1 argument.
This structural oversight bypassed the V2 query-conditioned semantics.

## Phase 10 - Security Trace Provenance
The fields `grounding_state`, `eligibility`, `decision`, and `trust_score` were all **DIRECT_RUNTIME** observations. They exactly matched the pipeline's execution path. There was no hardcoding. The execution was genuine; it just genuinely executed the flawed V1 logic.

## Phase 11 - Model/Retrieval Separation
The S-PubMedBERT model correctly returned broad semantic matches. The failure belongs entirely to the security controls (the grounding validator selection) failing to distinguish retrieval relevance from strict relationship grounding.

## Phase 12 - Two-Run RG-02 Reproducibility
Both runs produced identical outcomes. The behavior is **REPRODUCIBLY_INCORRECT**.

## Phase 13 - Final Decision
`RG02_SECURITY_RELEASE_ERROR`

## Phase 14 - Required Artifacts
Artifacts generated in `experiments/track_a_abstract_enriched_reannotation_v1/gate5_final_readiness_v2/`.

## Phase 15 - Readiness Status
`FULL_GATE5_MUST_REMAIN_STOPPED`.
The pipeline correctly executes, but it executes semantically invalid security checks for relationship grounding. Gate 5 cannot proceed until the harness is updated to use the V2 Grounding Validator and the correct aggregate gate logic is confirmed.
