# Canonical Relationship Identity Interface Impact

## 1. DrugNormalizerProtocol
- Currently returns `list[str]`.
- **Impact:** Must be updated to return `list[DrugEntity]` to preserve RxCUIs and source metadata for the orchestrator.

## 2. RAG Orchestrator
- Currently expects `query_drugs` to be strings.
- **Impact:** Needs to manage `DrugEntity` objects and explicitly construct the target `CanonicalRelationshipIdentity` prior to retrieval.

## 3. Relationship Grounding (RG-02)
- Currently takes raw text string candidates and parses using regex `_extract_entities_simple()`.
- **Impact:** Must be modified to accept `CanonicalRelationshipIdentity` as the expected query constraint and output an augmented `GroundingDecision` containing the canonical semantic mapping, not just `RelationshipGroundingStatus`.

## 4. EvidenceChunk
- Currently stores `relationship_scope: str | None`.
- **Impact:** Needs a new field: `relationship_identity: CanonicalRelationshipIdentity | None` to carry the bound semantics to the post-generation gate.

## 5. VerificationReportV2 / SemanticJudgment
- Currently relies on `nli_entailment` scores for semantic binding.
- **Impact:** `SemanticJudgment` must include an `identity_verification` field that strictly compares the claim's canonical graph against the source's canonical graph.

## Minimal Propagation Boundary (Recommendation)
To preserve architecture stability, the minimal boundary change is to add `relationship_identity: CanonicalRelationshipIdentity | None` to the `EvidenceChunk` and evaluate it purely as an exact-match structural check inside `ClaimVerifierV2`, falling back to NLI only for text nuance or when canonical forms cannot be resolved.
