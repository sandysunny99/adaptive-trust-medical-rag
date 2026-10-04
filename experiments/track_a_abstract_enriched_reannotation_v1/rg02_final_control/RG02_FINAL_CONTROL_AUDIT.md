# RG-02 FINAL CONTROL AUDIT
**Run timestamp:** 2026-09-30T18:37:15.225132+00:00

## Implementation Changes
1. Added `ENTITY_PAIR_MISMATCH` status to `RelationshipGroundingStatus`.
2. Added endpoint-alignment check: `q_ents.issubset(c_ents)` before contradiction/support checks.
3. Added `ENTITY_PAIR_MISMATCH` and `UNVERIFIABLE` to `EvidenceEligibilityGate` rejection list.
4. `_parse_intent` now emits `relation_type='UNKNOWN'` (not `IMPLICIT_MULTI_ENTITY`) for multi-entity queries without explicit relation keywords.
5. `doc_ctrl_unsupp` excluded from trusted registry — remains in retrieval corpus only.

## Security Invariant
**aligned_supporting_candidate_count == 0 => aggregate_eligibility != RELEASE:** HOLDS
**Violations:** None

## Case-ID Independence
Grep of `src/adaptive_trust_medical_rag/` for 'RG-02', 'POS-02', 'CTRL-UNSUPPORTED': **zero hits**.
Runtime grounding decisions are determined entirely by entity extraction + relation extraction + registry lookup.

## Trusted vs Untrusted Separation
| Fixture | In Retrieval Corpus | In Trusted Registry |
|---------|--------------------|--------------------|
| doc_rg02 | YES | YES |
| doc_pos01 | YES | YES |
| doc_pos02 | YES | YES |
| doc_ctrl_contra | YES | YES |
| doc_ctrl_unsupp | YES | **NO** |
| doc_ctrl_unrel | YES | YES |

## Per-Case Baseline Results (Run 1)
### RG-02
- Query: `Statin is a drug. Cyanide is a poison.`
- Retrieved: 5 candidates
- Aligned supporting: 0
- Aggregate: **BLOCK** (NO_QUERY_ALIGNED_SUPPORTING_EVIDENCE)
  - `doc_rg02_chunk_0`: NO_RELEVANT_RELATION / endpoint=MATCH
  - `doc_ctrl_unrel_chunk_0`: NO_RELEVANT_RELATION / endpoint=MISMATCH
  - `doc_pos01_chunk_0`: NO_RELEVANT_RELATION / endpoint=MISMATCH
  - `doc_ctrl_unsupp_chunk_0`: UNVERIFIABLE / endpoint=MISMATCH
  - `doc_pos02_chunk_0`: ENTITY_PAIR_MISMATCH / endpoint=MISMATCH

### REGRESSION-CRITICAL
- Query: `Does statin interact with cyanide?`
- Retrieved: 6 candidates
- Aligned supporting: 0
- Aggregate: **BLOCK** (NO_QUERY_ALIGNED_SUPPORTING_EVIDENCE)
  - `doc_ctrl_contra_chunk_0`: ENTITY_PAIR_MISMATCH / endpoint=MISMATCH
  - `doc_rg02_chunk_0`: NO_RELEVANT_RELATION / endpoint=MATCH
  - `doc_ctrl_unsupp_chunk_0`: UNVERIFIABLE / endpoint=MISMATCH
  - `doc_pos02_chunk_0`: ENTITY_PAIR_MISMATCH / endpoint=MISMATCH
  - `doc_pos01_chunk_0`: NO_RELEVANT_RELATION / endpoint=MISMATCH
  - `doc_ctrl_unrel_chunk_0`: NO_RELEVANT_RELATION / endpoint=MISMATCH

### POS-02
- Query: `Does statin interact with aspirin?`
- Retrieved: 6 candidates
- Aligned supporting: 1
- Aggregate: **RELEASE** (NONE)
  - `doc_ctrl_contra_chunk_0`: ENTITY_PAIR_MISMATCH / endpoint=MISMATCH
  - `doc_pos02_chunk_0`: SUPPORTED / endpoint=MATCH
  - `doc_ctrl_unsupp_chunk_0`: UNVERIFIABLE / endpoint=MISMATCH
  - `doc_pos01_chunk_0`: NO_RELEVANT_RELATION / endpoint=MISMATCH
  - `doc_ctrl_unrel_chunk_0`: NO_RELEVANT_RELATION / endpoint=MISMATCH
  - `doc_rg02_chunk_0`: NO_RELEVANT_RELATION / endpoint=MISMATCH

### CTRL-UNSUPPORTED
- Query: `Does statin interact with ibuprofen?`
- Retrieved: 6 candidates
- Aligned supporting: 0
- Aggregate: **BLOCK** (NO_QUERY_ALIGNED_SUPPORTING_EVIDENCE)
  - `doc_ctrl_contra_chunk_0`: ENTITY_PAIR_MISMATCH / endpoint=MISMATCH
  - `doc_ctrl_unsupp_chunk_0`: UNVERIFIABLE / endpoint=MISMATCH
  - `doc_ctrl_unrel_chunk_0`: NO_RELEVANT_RELATION / endpoint=MATCH
  - `doc_pos02_chunk_0`: ENTITY_PAIR_MISMATCH / endpoint=MISMATCH
  - `doc_pos01_chunk_0`: NO_RELEVANT_RELATION / endpoint=MISMATCH
  - `doc_rg02_chunk_0`: NO_RELEVANT_RELATION / endpoint=MISMATCH

### CTRL-CONTRADICTION
- Query: `Does metformin interact with aspirin?`
- Retrieved: 3 candidates
- Aligned supporting: 0
- Aggregate: **BLOCK** (NO_QUERY_ALIGNED_SUPPORTING_EVIDENCE)
  - `doc_ctrl_contra_chunk_0`: CONTRADICTED / endpoint=MATCH
  - `doc_pos02_chunk_0`: ENTITY_PAIR_MISMATCH / endpoint=MISMATCH
  - `doc_ctrl_unsupp_chunk_0`: UNVERIFIABLE / endpoint=MISMATCH

### POS-01
- Query: `statin therapy is common`
- Retrieved: 5 candidates
- Aligned supporting: 4
- Aggregate: **RELEASE** (NONE)
  - `doc_pos01_chunk_0`: SUPPORTED / endpoint=MATCH
  - `doc_ctrl_unrel_chunk_0`: SUPPORTED / endpoint=MATCH
  - `doc_rg02_chunk_0`: SUPPORTED / endpoint=MATCH
  - `doc_ctrl_unsupp_chunk_0`: UNVERIFIABLE / endpoint=MISMATCH
  - `doc_pos02_chunk_0`: SUPPORTED / endpoint=MATCH

## Cognee Results
- Any retrieved > 0: True
- Status: COGNEE_FINAL_CONTROL_VALIDATED

## Limitations
1. V2 validator uses deterministic keyword/regex entity and relation extraction — not generalized medical NLU.
2. Cognee retrieval may return 0 candidates if the GLiNER extraction pipeline does not produce searchable chunks for the test fixtures.
3. The trusted registry is constructed from test fixtures, not from the production FDA evidence corpus.
4. Full Gate 5 remains NOT PASSED / STOPPED.
