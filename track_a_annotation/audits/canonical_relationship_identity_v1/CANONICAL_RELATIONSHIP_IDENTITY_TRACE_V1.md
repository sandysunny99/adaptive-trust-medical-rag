# Canonical Relationship Identity Data Trace

| STAGE | INPUT | OUTPUT | CANONICAL RXCUI A | CANONICAL RXCUI B | RELATIONSHIP | PROVENANCE | PRESERVED? | EVIDENCE |
|---|---|---|---|---|---|---|---|---|
| Query Normalization | User Query string | `list[str]` (Orchestrator downcasts) | NO (downcast) | NO (downcast) | NO | NO | NO | `rag_orchestrator.py` L460 |
| Relationship Grounding (RG-02) | Query text, Chunk text | `GroundingDecision` with `entity_alignment` (strings) | NO | NO | Textual intent only | Chunk ID passed | NO | `relationship_grounding_v2.py` |
| Evidence Chunk Creation | `GroundingDecision.status` | `EvidenceChunk` | NO | NO | ONLY `status.name` (string) | Chunk ID | NO | `rag_orchestrator.py` L553 |
| Claim Verification | Generated claim, `EvidenceChunk` | `SemanticJudgment` | NO | NO | None (Uses NLI Entailment) | Citation ID | NO | `claim_verifier_v2.py` |
| Final Gate | `VerificationReportV2` | `RAGResponse` | NO | NO | None | None | NO | `rag_orchestrator.py` L586 |

## Identity Loss Point
The canonical identity is resolved inside `DrugNormalizer`, but is **immediately lost** inside `rag_orchestrator.py` because the orchestrator treats the normalizer output as `list[str]` instead of propagating the `DrugEntity` objects. Furthermore, `RG-02` re-extracts entities using regex strings, and `EvidenceChunk` entirely drops `entity_alignment`, keeping only the `RelationshipGroundingStatus`.
