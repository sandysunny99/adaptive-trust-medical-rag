# Canonical Relationship Identity Specification Reassessment

## 1. Context
The previous audit concluded a `SPECIFICATION_GAP` indicating that Canonical Relationship Identity was implicitly desired but structurally omitted from the software architecture design.

## 2. Documentation Findings
- **Directionality (`A -> B` vs `B -> A`)**: Explicitly required by `experiments/annotations/v3_1_human/annotation_guide.md` ("Note directionality: if A affects B, do not assume B affects A").
- **Canonical Drug Matching**: Explicitly required by `AGENTS.md` ("Never attribute evidence about Drug A to Drug B...").
- **Predicate/Interaction**: Explicitly required by `annotation_guide.md` ("Require evidence of the actual interaction").

## 3. Reassessment Conclusion
**SPECIFICATION_GAP_CONFIRMED**.
The core research objectives and annotation guidelines unequivocally demand exact drug-entity matching, explicit interaction predicates, and strict directionality. However, the software architecture specification completely omits a `CanonicalRelationshipIdentity` data structure required to enforce these rules.

## 4. Architectural Gap Confirmation
**ARCHITECTURAL_GAP_CONFIRMED**.
Because the software specification omitted the structure, the orchestrator code downcasts RxCUI to a string list, drops `entity_alignment` during EvidenceChunk creation, and relies entirely on unstructured textual Natural Language Inference (NLI) at the final gate. Textual NLI is fundamentally incapable of guaranteeing strict directionality or preventing subtle entity spoofing, rendering the architectural implementation inadequate for the documented research requirements.
