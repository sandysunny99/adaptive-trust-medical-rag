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
