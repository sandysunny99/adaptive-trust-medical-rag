# RG-02 Aggregate Grounding Audit

## 1. Expected Aggregate Release Logic
Per the established RG-02 protocol and V2 validator specification, a multi-entity query requires query-aligned supporting evidence to pass the Evidence Eligibility Gate.
- If Candidate A supports `statin-aspirin` and Candidate B supports `metformin-insulin`, both represent `ENTITY_PAIR_MISMATCH` relative to the query `statin-cyanide`.
- The aggregate query state must be `NO_QUERY_ALIGNED_SUPPORT`.
- The final orchestrator decision must be `BLOCK` / `UNVERIFIABLE`.

## 2. Actual Runtime Behavior
In the Final Readiness Validation V1 trace:
- Four candidates were retrieved (`chunk-spironolactone-001`, `chunk-metformin-001`, `chunk-warfarin-001`, `chunk-haloperidol-001`).
- The V1 `RelationshipGroundingValidator` evaluated each candidate. It only checked if the candidate text was supported by the document source, without comparing it to the query endpoints.
- Thus, all candidates were marked `SUPPORTED`.
- The `EvidenceEligibilityGate` received a list of 4 `SUPPORTED` candidates. Since they also passed the trust threshold (0.57-0.58 >= 0.45), the gate marked `eligible_count = 4` and aggregate `passed = true`.
- The orchestrator emitted `status = released` and `gate_decision = release`.

## 3. Conclusion
An unrelated supported candidate **incorrectly upgraded** the aggregate query to `RELEASE`. The semantic correctness of the relationship grounding failed because the V1 validator was used, which lacks the query-level entity alignment checks required by the RG-02 protocol.
