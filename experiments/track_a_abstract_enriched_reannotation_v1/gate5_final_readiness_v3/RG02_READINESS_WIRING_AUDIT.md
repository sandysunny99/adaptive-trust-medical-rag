# RG-02 Readiness Wiring Audit

## 1. Trace of `RelationshipGroundingValidatorV2`
The V2 validator is now correctly wired into the final readiness harness:

- **Initialization**: `experiments/gate5_readiness_v3.py` explicitly imports `RelationshipGroundingValidatorV2` from `adaptive_trust_medical_rag.security_extensions.relationship_grounding_v2` (Line 42) and instantiates it for both runs (Lines 263, 349).
- **Retrieval & Candidate Evaluation**: The harness evaluates each candidate directly: `grounding_dec = grounding_val.validate(cand, query=query)` (Line 275). It explicitly passes `query=query`.
- **Orchestrator Integration**: `rag_orchestrator.py` correctly passes the `query` argument (Lines 534-535) because `inspect.signature` detects the `query` parameter on the V2 instance.
- **EvidenceEligibilityGate**: The gate maps V2 status codes (`ENTITY_PAIR_MISMATCH`, `NO_RELEVANT_RELATION`) to the rejection reason `'RELATIONSHIP_GROUNDING_UNSUPPORTED'` and correctly blocks the candidates.

## 2. V1 Override Removed
The historical `RelationshipGroundingValidator` (V1) is no longer imported or instantiated anywhere in the active `gate5_readiness_v3.py` execution path. The import was cleanly replaced.

## 3. Results of Wiring Repair
Because the correct V2 validator is instantiated and the query string is preserved down to the validation layer, candidates that discuss unrelated entity pairs (like statin-aspirin) now fail entity-pair alignment (`ENTITY_PAIR_MISMATCH`). 
As a result, no candidates pass the grounding gate for RG-02, and the orchestrator properly returns `status=abstained`.
