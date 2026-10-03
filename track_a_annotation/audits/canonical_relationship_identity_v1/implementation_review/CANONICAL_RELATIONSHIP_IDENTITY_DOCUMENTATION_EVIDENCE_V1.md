# Canonical Relationship Identity Documentation Evidence V1

## RXCUI
**DOCUMENT:** `reports/audit/biomedical_api_evaluation.md`
**SECTION:** `1. Candidate Evaluation Matrix`
**SHORT QUOTE:** "NLM RxNorm / RxNav | Drug Normalization | RxCUI resolution, brand/generic mapping | Critical (Drug entity grounding)"
**REQUIREMENT:** The architecture must use RxNorm RxCUI resolution for critical drug entity grounding.
**EVIDENCE TYPE:** EXPLICIT
**IMPLEMENTATION CONSEQUENCE:** The RxCUI resolved by the normalizer must be propagated structurally.

## CANONICAL_DRUG_IDENTITY
**DOCUMENT:** `AGENTS.md`
**SECTION:** `2. Absolute Safety & Grounding Directives`
**SHORT QUOTE:** "Entity Match: Never attribute evidence about Drug A to Drug B, or conflate different formulations/salts/routes of administration."
**REQUIREMENT:** The system must strictly separate discrete drug identities and never cross-attribute claims.
**EVIDENCE TYPE:** EXPLICIT
**IMPLEMENTATION CONSEQUENCE:** Unstructured text matching is insufficient; canonical identities are required to enforce absolute entity separation.

## CANONICAL_DRUG_PAIR
**DOCUMENT:** `experiments/annotations/v3_1_human/annotation_guide.md`
**SECTION:** `Specific Domain Rules`
**SHORT QUOTE:** "DDI: Require evidence of the actual interaction... A document that merely mentions both drugs is NOT_RELEVANT."
**REQUIREMENT:** Ground truth requires the explicit semantic pair to be bound.
**EVIDENCE TYPE:** EXPLICIT
**IMPLEMENTATION CONSEQUENCE:** Identity must encompass both the subject and object drug entities explicitly.

## RELATIONSHIP_PREDICATE
**DOCUMENT:** `experiments/annotations/v3_1_human/annotation_guide.md`
**SECTION:** `Specific Domain Rules`
**SHORT QUOTE:** "DDI: Require evidence of the actual interaction (e.g., increases exposure, reduces clearance, contraindicated)."
**REQUIREMENT:** The interaction predicate must be proven.
**EVIDENCE TYPE:** EXPLICIT
**IMPLEMENTATION CONSEQUENCE:** The canonical identity must store and compare the specific predicate, not just a binary relation.

## DIRECTIONALITY
**DOCUMENT:** `experiments/annotations/v3_1_human/annotation_guide.md`
**SECTION:** `Specific Domain Rules`
**SHORT QUOTE:** "Note directionality: if A affects B, do not assume B affects A."
**REQUIREMENT:** Pharmacological interactions must be evaluated directionally, distinguishing subject and object.
**EVIDENCE TYPE:** EXPLICIT (ANNOTATION REQUIREMENT that drives system goals)
**IMPLEMENTATION CONSEQUENCE:** The architecture must preserve and explicitly verify the subject-object direction (A -> B).

## PROVENANCE
**DOCUMENT:** `reports/security/threat_model.md`
**SECTION:** `TM-03 Retrieval Poisoning`
**SHORT QUOTE:** "SHA-256 Provenance Check" and "Malicious document placed in vector index"
**REQUIREMENT:** Tracking of evidence provenance is strictly required against poisoned documents.
**EVIDENCE TYPE:** EXPLICIT
**IMPLEMENTATION CONSEQUENCE:** The canonical identity check must bind to the existing evidence-chunk-level provenance.

## ABSTENTION
**DOCUMENT:** `AGENTS.md`
**SECTION:** `2. Absolute Safety & Grounding Directives`
**SHORT QUOTE:** "When evidence is missing... or unresolvably contradictory, the system must abstain"
**REQUIREMENT:** The system must fail-closed on missing or contradictory evidence.
**EVIDENCE TYPE:** EXPLICIT
**IMPLEMENTATION CONSEQUENCE:** A failure to match canonical identity triggers an explicit UNSUPPORTED or AMBIGUOUS state, routing to abstention.

## SECURITY
**DOCUMENT:** `reports/security/retrieval_poisoning_evaluation.md`
**SECTION:** `Retrieval Poisoning & Source Integrity Evaluation`
**SHORT QUOTE:** "Entity Misattribution | Compound A safety profile assigned to Compound B"
**REQUIREMENT:** The system must defend against text claiming false entity assertions.
**EVIDENCE TYPE:** EXPLICIT
**IMPLEMENTATION CONSEQUENCE:** A canonical check is required to protect the final gate against misattribution.

## CLAIM_IDENTITY_BINDING
**DOCUMENT:** `AGENTS.md`
**SECTION:** `2. Absolute Safety & Grounding Directives`
**SHORT QUOTE:** "Every factual medical claim must be grounded in retrieved, verifiable evidence."
**REQUIREMENT:** Generated claims must reflect the source evidence precisely.
**EVIDENCE TYPE:** IMPLICIT
**IMPLEMENTATION CONSEQUENCE:** While the exact data contract isn't specified, the explicit requirement demands exact relationship-specific grounding.

## TEST_REQUIREMENT
**DOCUMENT:** N/A
**SECTION:** N/A
**SHORT QUOTE:** N/A
**REQUIREMENT:** Comprehensive adversarial testing is implicitly required by security benchmarks.
**EVIDENCE TYPE:** IMPLICIT
**IMPLEMENTATION CONSEQUENCE:** Targeted testing for entity, direction, and predicate mismatch must be introduced.
