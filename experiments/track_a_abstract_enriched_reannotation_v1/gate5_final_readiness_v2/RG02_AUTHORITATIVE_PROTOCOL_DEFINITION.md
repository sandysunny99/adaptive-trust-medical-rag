# RG-02 Authoritative Protocol Definition

## 1. Identity & Classification
- **Case ID:** `RG-02`
- **Control Classification:** Negative Control (Unsupported Relationship)
- **Role:** Exercises the Relationship Grounding & Claim-Specific Evidence Sufficiency boundary.

## 2. Queries
- **Canonical Query (V2):** `"Statin is a drug. Cyanide is a poison."`
- **Regression Query:** `"Does statin interact with cyanide?"`

## 3. Relationship Semantics
- **Entity Pair Endpoints:** `("statin", "cyanide")`
- **Expected Grounding Behavior:** 
  - A candidate providing factual co-occurrence without a relationship must evaluate to `NO_RELEVANT_RELATION`.
  - A candidate supporting a different entity pair (e.g., statin and aspirin) must evaluate to `ENTITY_PAIR_MISMATCH`.
- **Allowed Supporting Evidence:** None. No valid medical source establishes an interaction between statin and cyanide.
- **Forbidden Evidence:** Any candidate asserting an unrelated relationship must NOT upgrade the query to a `SUPPORTED` state.

## 4. Expected Outcome
- **Aggregate Gate Decision:** `BLOCK` (`NO_QUERY_ALIGNED_SUPPORTING_EVIDENCE` or `RELATIONSHIP_GROUNDING_UNSUPPORTED`).
- **Security Invariant:** `aligned_supporting_candidate_count == 0 => aggregate_eligibility != RELEASE`

## 5. Protocol Source Provenance
- `experiments/track_a_abstract_enriched_reannotation_v1/rg02_grounding_v2/RG02_GROUNDING_V2_SPEC.md`
- `experiments/track_a_abstract_enriched_reannotation_v1/rg02_final_control/RG02_FINAL_CONTROL_AUDIT.md`
