# COGNEE FINAL CONTROL AUDIT
**Run Timestamp:** 2026-09-30T18:51:25.384147+00:00

## Validation Summary
- Overall Status: COGNEE_TARGETED_CONTROL_VALIDATED
- Identity Bridge Functional: True
- POS-02 Released: True
- RG-02 Blocked: True
- Unsupported Blocked: True
- Contradiction Blocked: True

## Results Detail
### POS-02
- Retrieved: 6
- Aligned Support: 1
- Aggregate Eligibility: **RELEASE** (NONE)

  - **doc_pos02_chunk_0**
    - Relation: INTERACTS_WITH
    - Endpoint Alignment: MATCH
    - Grounding: SUPPORTED
  - **doc_ctrl_unsupp_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: UNVERIFIABLE
  - **doc_ctrl_contra_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: UNVERIFIABLE
  - **doc_pos01_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: NO_RELEVANT_RELATION
  - **doc_ctrl_unrel_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: NO_RELEVANT_RELATION
  - **doc_rg02_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: UNVERIFIABLE

### RG-02
- Retrieved: 6
- Aligned Support: 0
- Aggregate Eligibility: **BLOCK** (NO_QUERY_ALIGNED_SUPPORTING_EVIDENCE)

  - **doc_rg02_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: UNVERIFIABLE
  - **doc_ctrl_unrel_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: NO_RELEVANT_RELATION
  - **doc_pos01_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: NO_RELEVANT_RELATION
  - **doc_pos02_chunk_0**
    - Relation: INTERACTS_WITH
    - Endpoint Alignment: MISMATCH
    - Grounding: ENTITY_PAIR_MISMATCH
  - **doc_ctrl_unsupp_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: UNVERIFIABLE
  - **doc_ctrl_contra_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: UNVERIFIABLE

### CTRL-UNSUPPORTED
- Retrieved: 6
- Aligned Support: 0
- Aggregate Eligibility: **BLOCK** (NO_QUERY_ALIGNED_SUPPORTING_EVIDENCE)

  - **doc_ctrl_unsupp_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: UNVERIFIABLE
  - **doc_pos02_chunk_0**
    - Relation: INTERACTS_WITH
    - Endpoint Alignment: MISMATCH
    - Grounding: ENTITY_PAIR_MISMATCH
  - **doc_ctrl_unrel_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MATCH
    - Grounding: NO_RELEVANT_RELATION
  - **doc_pos01_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: NO_RELEVANT_RELATION
  - **doc_ctrl_contra_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: UNVERIFIABLE
  - **doc_rg02_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: UNVERIFIABLE

### CTRL-CONTRADICTION
- Retrieved: 6
- Aligned Support: 0
- Aggregate Eligibility: **BLOCK** (NO_QUERY_ALIGNED_SUPPORTING_EVIDENCE)

  - **doc_ctrl_contra_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: UNVERIFIABLE
  - **doc_pos02_chunk_0**
    - Relation: INTERACTS_WITH
    - Endpoint Alignment: MISMATCH
    - Grounding: ENTITY_PAIR_MISMATCH
  - **doc_ctrl_unsupp_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: UNVERIFIABLE
  - **doc_pos01_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: NO_RELEVANT_RELATION
  - **doc_ctrl_unrel_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: NO_RELEVANT_RELATION
  - **doc_rg02_chunk_0**
    - Relation: NONE
    - Endpoint Alignment: MISMATCH
    - Grounding: UNVERIFIABLE
