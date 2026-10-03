# Canonical Relationship Identity Requirement Trace V1

## Requirement Matrix

| Requirement | Documentation Evidence | Evidence Type | Current Implementation | Current Tests | Gap Classification | Implementation Implication |
|---|---|---|---|---|---|---|
| RxCUI canonicalization | `AGENTS.md`, `biomedical_api_evaluation.md` | EXPLICIT | Downcast to string | None | ARCHITECTURAL_GAP | Required |
| Canonical drug identity | "Never attribute evidence about Drug A to Drug B" (`AGENTS.md`) | EXPLICIT | Regex string match | None | ARCHITECTURAL_GAP | Required |
| Canonical drug pair | DDI Evaluation Guidelines | EXPLICIT | Strings inside RG-02 | None | ARCHITECTURAL_GAP | Required |
| Relationship predicate | "Require evidence of the actual interaction" (`annotation_guide.md`) | EXPLICIT | Text NLI / String regex | Textual overlap | ARCHITECTURAL_GAP | Required |
| Relationship direction | "Note directionality: if A affects B, do not assume B affects A" | EXPLICIT | Text NLI (very weak on direction) | None | ARCHITECTURAL_GAP | Required |
| Relationship scope | `RG-02` block (`NO_RELEVANT_RELATION`) | EXPLICIT | Status string propagated | Status checks | NO_GAP | N/A |
| Claim identity binding | "Every factual medical claim must trace..." (`AGENTS.md`) | IMPLICIT | NLI entailment | Textual entailment | ARCHITECTURAL_GAP | Required |
| Evidence identity binding | Provenance & citation rule | IMPLICIT | Status string only | None | ARCHITECTURAL_GAP | Required |
| Provenance | "SHA-256 Provenance & Authority Tiering" | EXPLICIT | Source ID mapped, but semantic pair not tracked | Provenance checks | SPECIFICATION_GAP | Required |
| Abstention | "When evidence is missing... must abstain" (`AGENTS.md`) | EXPLICIT | Status triggers abstention | Yes | NO_GAP | N/A |
| Security | "Entity Misattribution" (`retrieval_poisoning_evaluation.md`) | EXPLICIT | NLI / Regex | None for direction | ARCHITECTURAL_GAP | Required |
| Testing | Test coverage required for security | IMPLICIT | No canonical ID tests | None | TEST_COVERAGE_GAP | Required |
