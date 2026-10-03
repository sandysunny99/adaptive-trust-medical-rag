# Canonical Relationship Identity Dataflow Specification V1

## 1. Structure Definition
```python
@dataclass
class CanonicalRelationshipIdentity:
    subject_rxcui: str
    object_rxcui: str
    predicate: str
    direction: str  # e.g., 'A_TO_B', 'B_TO_A', 'BIDIRECTIONAL'
    provenance_chunk_id: Optional[str] = None
```
**Justification**: Smallest possible data contract to satisfy the explicit annotation requirements for exact entity, explicit interaction, and strict directionality tracking, carrying provenance.

## 2. Propagation Flow
1. **`rag_orchestrator.py` (Pre-Retrieval)**:
   - Receives `DrugEntity` from `DrugNormalizerProtocol`.
   - Constructs `CanonicalRelationshipIdentity` dynamically if an interaction is queried.
2. **`EvidenceChunk`**:
   - Accepts `relationship_identity: Optional[CanonicalRelationshipIdentity] = None`.
   - Populated from the orchestrator before hitting the Claim Verifier.
3. **`ClaimVerifierV2`**:
   - Parses the generated claim to establish a semantic structure.
   - Deterministically compares the claim's identity against the `EvidenceChunk`'s canonical identity.
   - Outputs the structural match result into `SemanticJudgment`.
4. **`AnswerSafetyGate`**:
   - Receives `SemanticJudgment`. 

## 3. RG-02 Isolation
`RG-02` (Relationship Grounding V2) remains **unchanged**. It operates strictly as a text-based relevance filter and generates statuses (`SUPPORTED`, `UNSUPPORTED`). The `CanonicalRelationshipIdentity` bypasses RG-02 and is attached directly to the `EvidenceChunk` by the Orchestrator, avoiding architectural rewrite of the grounding engine.
