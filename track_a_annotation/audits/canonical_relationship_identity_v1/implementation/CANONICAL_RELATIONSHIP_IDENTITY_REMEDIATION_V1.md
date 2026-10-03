# Canonical Relationship Identity Remediation V1

## Problem
The Adaptive Trust-Aware Medical RAG pipeline lost canonical drug relationship identity (RxCUI, predicate, direction) at two points:
1. **LOSS_POINT_A**: `rag_orchestrator.py` Step 2 — `DrugNormalizerProtocol.normalize()` returns `list[str]`, discarding `DrugEntity.rxcui`.
2. **LOSS_POINT_B**: `rag_orchestrator.py` Step 8 — `EvidenceChunk` creation retained only `grounding_states[chunk_id].status.name`, discarding structural relationship identity.

## Root Cause
The original architecture treated drug entity resolution and relationship grounding as textual status signals rather than structural identity objects. Post-generation verification (NLI) checked semantic entailment without deterministic entity/predicate/direction binding.

The current NLI-based verification path does not structurally encode canonical subject, predicate, object, and direction, so it cannot provide a deterministic canonical-identity binding guarantee.

## Design
### Data Contract
```python
@dataclass(frozen=True)
class CanonicalRelationshipIdentity:
    subject_rxcui: str        # Canonical RxNorm identifier for subject drug
    object_rxcui: str         # Canonical RxNorm identifier for object drug
    predicate: str            # Normalized interaction predicate (bounded set)
    direction: CanonicalDirection  # A_TO_B | B_TO_A | BIDIRECTIONAL | UNKNOWN
    provenance_chunk_id: str | None = None  # Evidence chunk establishing identity
```

### Identity Status Model
- **MATCH**: All four identity fields match exactly → proceed to NLI/citation/trust verification
- **MISMATCH**: Any field differs → UNSUPPORTED → AnswerSafetyGate → controlled abstention
- **AMBIGUOUS**: Cannot resolve claim identity → UNSUPPORTED → controlled failure
- **UNAVAILABLE**: Source or claim identity missing → UNSUPPORTED → controlled failure

### Canonicalization Source
Uses the existing `DrugNormalizer` / `EntityCache` canonicalization path. No independent RxNorm lookup mechanism created.

### Propagation Path
```
DrugNormalizer → DrugEntity(RxCUI) → drug_rxcui_map → CanonicalRelationshipIdentity
    → EvidenceChunk.relationship_identity → ClaimVerifierV2 → SemanticJudgment
    → AnswerSafetyGate → RELEASE / ABSTAIN
```

## Claim Binding
- Deterministic regex-based extraction resolves claim subject, object, predicate, and direction
- Exact string equality on all four canonical fields (no fuzzy/embedding/NLI similarity)
- Ambiguous or unresolved parsing fails closed (does NOT fall back to NLI and release)

## Abstention Integration
Canonical identity failures map to existing `FinalSupportState.UNSUPPORTED`, which routes through the existing `AnswerSafetyGate` controlled abstention mechanism. No second abstention system created.

## Security Controls
The implementation adds deterministic canonical identity validation for the tested subject, object, predicate, and direction mismatch classes. The control complements semantic NLI rather than replacing it.

## Limitations
- Canonical identity validation does not prove pharmacological relationship clinical correctness
- It verifies identity consistency between canonical evidence and generated claim relationships
- Claim extraction is regex-based and may not resolve all claim structures
- Predicate normalization uses a bounded set; unmapped predicates are uppercased as-is
- Direction determination relies on text position ordering

## Backward Compatibility
- `EvidenceChunk.relationship_identity` defaults to `None` (backward compatible)
- `SemanticJudgment.canonical_identity_status/reason` defaults to `None` (backward compatible)
- `ClaimVerifierV2.verify()` accepts optional `drug_rxcui_map` (backward compatible)
- All existing NLI, citation, trust, and RG-02 semantics preserved
- No changes to RG-02, Trust P0 V2, Controlled Abstention V1, or Track A
