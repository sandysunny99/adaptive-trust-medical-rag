# Canonical Relationship Identity Audit V1 - Executive Summary

## 1. Executive Summary
This audit investigated the architectural propagation of Canonical Relationship Identity (RxCUI A + predicate + RxCUI B) within the Adaptive Trust-Aware Medical RAG pipeline. The audit confirmed that while the pipeline resolves RxCUIs during normalization, and identifies textual relationship statuses during Relationship Grounding (RG-02), the explicit, canonical semantic identity of the relationship is entirely lost before evidence evaluation and never structurally bound to the final generated claim.

## 2. Current Repository State
- **HEAD:** 5b2d985879ad6592b30e15a47ca2412ef9694055
- **BRANCH:** main
- **TRACK A:** 530/530 UNCHANGED
- **RETRIEVAL:** FROZEN
- **PRODUCTION CODE:** UNCHANGED

## 3. Existing RG-02 Behavior
- RG-02 takes the `Candidate` and `query` strings.
- It uses regex-based heuristic extraction `_extract_entities()` to find string arrays of drug names (e.g. `["aspirin", "warfarin"]`).
- It extracts broad predicates `_extract_relations()` (e.g. `interaction`, `contraindication`).
- It produces a `RelationshipGroundingStatus` (e.g., `SUPPORTED`, `UNSUPPORTED`, `NO_RELEVANT_RELATION`).
- It returns an `entity_alignment` map of strings, but **does not output canonical RxCUI identifiers** or a canonical relationship structure.

## 4. Existing RxNorm/RxCUI Behavior
- The `DrugNormalizer` (in `normalization/drug_normalizer.py`) successfully maps raw text into a canonical `DrugEntity` containing an `rxcui` field.
- However, `rag_orchestrator.py` downcasts this resolution to just a `list[str]` (names) via `query_drugs = self._drug_normalizer.normalize(...)`.

## 5. End-to-End Relationship Data Trace
See `CANONICAL_RELATIONSHIP_IDENTITY_TRACE_V1.md` for full data flow.
- Query Parsing → DrugNormalizer (Creates RxCUI)
- Orchestrator → Casts RxCUI to string names
- RG-02 → Uses regex, outputs `RelationshipGroundingStatus`
- EvidenceChunk → Stores only string `status.name` (e.g., "SUPPORTED")
- ClaimVerifierV2 → Checks NLI textual entailment and reads status string.

## 6. Exact Identity-Loss Point
The exact loss point is **DURING EVIDENCE OBJECT CREATION** (and practically during RG-02 orchestration). `EvidenceChunk` instantiation takes `grounding_states[chunk_id].status.name`, completely discarding the underlying entities (canonical or textual).

## 7. Current Final-Claim Binding Behavior
- `ClaimVerifierV2` uses text-based NLI to establish textual entailment (`SemanticJudgment`).
- It checks if `relationship_scope == "UNSUPPORTED"`.
- It **does not** extract the canonical Subject/Predicate/Object from the generated claim and compare it against the source CanonicalRelationshipIdentity.

## 8. Specification Status
- Explicit canonical relationship propagation is implicitly referenced as a research goal but lacks an explicit architectural specification defining `CanonicalRelationshipIdentity`.

## 9. Final Gap Classification
**ARCHITECTURAL_GAP** (Specifically: A Propagation and Final Claim Binding Gap). The system handles statuses but structurally loses the identity semantics needed to verify that the generated text describes the exact same entities and predicate as the source evidence.

## 10. Recommendation
**ARCHITECTURAL REMEDIATION REQUIRED**
