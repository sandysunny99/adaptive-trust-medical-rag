# Canonical Relationship Identity Audit & Review

Below is the consolidated data from the architectural gap assessment and the documentation review.

## 1. Architectural Audit (`CANONICAL_RELATIONSHIP_IDENTITY_AUDIT_V1.md`)

```markdown
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
```

---

## 2. Documentation Review (`CANONICAL_RELATIONSHIP_IDENTITY_DOCUMENTATION_REVIEW_V1.md`)

```markdown
# Canonical Relationship Identity Documentation Review V1

## 1. Executive Summary
This documentation-first forensic review investigated whether the project's Markdown documentation, research notes, and guidelines explicitly require Canonical Relationship Identity binding. The review confirms that the core research requirements and human annotation guidelines *explicitly demand* exact drug identity matching, actual interaction evidence, and strict directionality verification. However, the software architecture specification omitted a formal `CanonicalRelationshipIdentity` object to enforce these rules structurally.

## 2. Methodology
Executed targeted semantic `git grep` queries across all Markdown files to extract explicit and implicit requirements regarding RxCUIs, drug pairs, directionality, and claim verification.

## 3. Findings
- **RxCUI Canonicalization**: EXPLICITLY REQUIRED (e.g. `AGENTS.md`, `biomedical_api_evaluation.md`).
- **Canonical Drug Pair**: EXPLICITLY REQUIRED.
- **Directionality**: EXPLICITLY REQUIRED (`experiments/annotations/v3_1_human/annotation_guide.md` explicitly forbids assuming symmetric relationships: "if A affects B, do not assume B affects A").
- **Claim Identity Binding**: IMPLICITLY REQUIRED ("Every factual medical claim must be grounded... Never attribute evidence about Drug A to Drug B").
- **Provenance**: EXPLICITLY REQUIRED for chunk text, but semantic pairs lack documented provenance integration (a specification gap).

## 4. Re-evaluation of Previous Audit Claims
- **SPECIFICATION_GAP**: CONFIRMED. The rules demand strict entity and directional matching, but the architectural design specs provide no data structure to accomplish this.
- **ARCHITECTURAL_GAP**: CONFIRMED. The implementation downcasts RxCUIs and relies entirely on unstructured textual Natural Language Inference (NLI) at the final gate. Textual NLI is fundamentally incapable of guaranteeing strict directionality or preventing subtle entity spoofing as demanded by the annotation guidelines.

## 5. Implementation Justification
**YES**. Implementation is justified because the explicit annotation guides and core rules demand exact entity, exact interaction, and exact direction matching, which the current unstructured textual entailment (NLI) architecture structurally cannot guarantee.

The minimum required implementation boundary involves introducing a `CanonicalRelationshipIdentity` structure (with Subject RxCUI, Object RxCUI, Predicate, and Direction), carrying it through the `EvidenceChunk`, and explicitly comparing it during `ClaimVerifierV2`.

## 6. Final Recommendation
**PROCEED_TO_IMPLEMENTATION_REVIEW**
```
