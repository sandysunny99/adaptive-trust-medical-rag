# Canonical Relationship Identity Implementation Review V1

## 1. Executive Summary
This final specification adjudication converts the prior documentation and architectural audits into a precise, source-supported implementation specification for Canonical Relationship Identity. Markdown documentation explicitly requires RxCUI alignment, exact drug pairs, and directionality to prevent misattribution and adversarial spoofing. 

The implementation gap is confirmed across `rag_orchestrator.py` and `EvidenceChunk`. The post-generation verification structurally relies on textual NLI, which does not structurally encode canonical subject, predicate, object, and direction, so it cannot provide a deterministic canonical-identity binding guarantee. The implementation fixes this by injecting deterministic constraints that precede the semantic NLI.

## 2. Requirement Reassessment
- **RxCUI**: EXPLICIT (`biomedical_api_evaluation.md`)
- **Canonical Drug Identity**: EXPLICIT (`AGENTS.md`)
- **Canonical Drug Pair**: EXPLICIT (`annotation_guide.md`)
- **Predicate**: EXPLICIT (`annotation_guide.md`)
- **Direction**: EXPLICIT (`annotation_guide.md`: "if A affects B, do not assume B affects A")
- **Claim Identity Binding**: IMPLICIT (Derived from core evidence grounding rules)
- **Provenance**: EXPLICIT (Derived from ingestion requirements)
- **Abstention**: EXPLICIT (`AGENTS.md`)
- **Security**: EXPLICIT (`retrieval_poisoning_evaluation.md`: Entity Misattribution)
- **Test Requirement**: IMPLICIT (Implied by security benchmark)

## 3. Specification Gap Refinement
**FORMAL ARCHITECTURAL SPECIFICATION GAP = CONFIRMED**. The explicit business/research requirements exist and are well-documented, but the software Data Model, Implementation Contract, and Test Contract defining how to structurally enforce them were omitted.

## 4. Exact Identity Loss Points
1. **LOSS_POINT_1**: `rag_orchestrator.py` -> `query_drugs`. Downcasts the `DrugEntity` containing RxCUIs to a `list[str]`. Canonical identity is discarded before being attached to chunk evaluation.
2. **LOSS_POINT_2**: `rag_orchestrator.py` -> `EvidenceChunk` creation. Retains `grounding_states[chunk_id].status.name` but discards any underlying entity structural relationship.

## 5. Claim Binding & Security Finding
Textual NLI can assess semantic entailment, but the current implementation does not provide a deterministic canonical entity/predicate/direction binding guarantee. 

The risk of "Correct source + wrong relationship interpretation" (where NLI fails to catch a hallucinated direction reversal or adversarial entity spoof) is **PLAUSIBLE**. A deterministic canonical identity check reduces a class of entity/predicate/direction mismatch risk.

## 6. Ambiguity Rule
Unresolved or ambiguous canonical identity parsing must **NOT** silently fall through to NLI. It must explicitly trigger an `UNSUPPORTED` or `AMBIGUOUS` state that results in Controlled Abstention.

## 7. Implementation Boundary
The implementation boundary includes:
- `rag_orchestrator.py`
- `EvidenceChunk`
- `claim_verifier_v2.py`
- `SemanticJudgment`
(along with defining `CanonicalRelationshipIdentity` in a types module)

## 8. Final Decision
**PROCEED_TO_IMPLEMENTATION**
