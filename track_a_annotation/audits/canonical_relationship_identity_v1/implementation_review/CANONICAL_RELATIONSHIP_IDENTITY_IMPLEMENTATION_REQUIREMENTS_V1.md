# Canonical Relationship Identity Implementation Requirements V1

| Requirement | Source Evidence | Current State | Gap | Required Change | Affected Component | Backward Compatibility | Required Test |
|---|---|---|---|---|---|---|---|
| Canonical subject RxCUI | `AGENTS.md` | Discarded | Target identity lost | Pass `DrugEntity`/RxCUI | `rag_orchestrator.py` | Add to evidence object | Exact RxCUI match |
| Canonical object RxCUI | `AGENTS.md` | Discarded | Target identity lost | Pass `DrugEntity`/RxCUI | `rag_orchestrator.py` | Add to evidence object | Exact RxCUI match |
| Relationship predicate | `annotation_guide.md` | Textual status only | Semantic predicate lost | Store canonical predicate | `EvidenceChunk` | Optional extension | Predicate mismatch |
| Direction | `annotation_guide.md` | Textual order | Reversible by NLI | Store directional flag | `EvidenceChunk` | Optional extension | Direction reversal |
| Relationship scope | `relationship_grounding_v2` | Status string | None | N/A | None | N/A | N/A |
| Evidence binding | `AGENTS.md` | Text bound only | Semantic binding missing | `CanonicalRelationshipIdentity` attached | `EvidenceChunk` | Optional field addition | End-to-end trace |
| Claim binding | Inferred rule | NLI Entailment | Identity unchecked | Add `identity_verification` | `claim_verifier_v2.py` | Extend `SemanticJudgment` | Claim identity match |
| Provenance | Inferred rules | String chunk traced | Semantic provenance absent | Trace identity to chunk ID | `SemanticJudgment` | Extend `SemanticJudgment` | Identity provenance |
| Abstention | `AGENTS.md` | Status-based | Mismatch bypasses block | Map ambiguity/mismatch to UNSUPPORTED | `claim_verifier_v2.py` | Maps to existing state | Block on mismatch |
| Security | `threat_model.md` | NLI text defense | NLI spoofable | Structural check before NLI | `claim_verifier_v2.py` | Additive check | Adversarial NLI bypass |
| Testing | Inferred | Missing | No canonical tests | Add targeted unit tests | `tests/` | Additive only | All identity cases |
