# Canonical Relationship Identity Documentation Search Log V1

## 1. Search Query: RxCUI / Canonical Drug Identity
**Command:** `git grep -n -i -E "RxCUI|RxNorm|canonical drug|canonical entity|drug entity|drug pair" -- "*.md"`
**Hits:** High volume (50+ hits)
**Relevant Sections:**
- `AGENTS.md`: "Never attribute evidence about Drug A to Drug B, or conflate different formulations/salts/routes of administration."
- `reports/audit/biomedical_api_evaluation.md`: "RxCUI resolution, brand/generic mapping | Critical (Drug entity grounding)"
- `reports/research/novelty_positioning.md`: "RxNorm entity attribution matching."
- `reports/security/retrieval_poisoning_evaluation.md`: "Entity Misattribution | Compound A safety profile assigned to Compound B | RxCUI"

## 2. Search Query: Directionality
**Command:** `git grep -n -i -E "direction|directional|subject|object|symmetric|asymmetric|A.?B|B.?A" -- "*.md"`
**Hits:** Moderate
**Relevant Sections:**
- `experiments/annotations/v3_1_human/annotation_guide.md:17`: "- **DDI**: Require evidence of the actual interaction (e.g., increases exposure, reduces clearance, contraindicated). A document that merely mentions both drugs is `NOT_RELEVANT`. Note directionality: if A affects B, do not assume B affects A."
**Interpretation:** This is a definitive, explicit requirement that directionality and exact interaction semantics must be verified.

## 3. Search Query: Claim Verification
**Command:** `git grep -n -i "claim verif" -- "*.md"`
**Hits:** High
**Relevant Sections:**
- `reports/research/final_research_report.md`: "Post-generation verification catches 100% of fabricated PMIDs/URLs and 98.9% of unsupported claims."
- `experiments/guardrail_enhancement/COMPONENT_OVERLAP_MATRIX.md`: "Custom verifier uses specific medical NLI logic (contradiction vs neutral vs entailment)."

## 4. Search Query: Relationship Identity
**Command:** `git grep -n -i -E "relationship identity|canonical relationship" -- "*.md"`
**Hits:** 5 hits
**Relevant Sections:**
- `track_a_annotation/audits/claim_evidence_remediation_v1/CLAIM_EVIDENCE_REMEDIATION_FINAL_CLOSE_REPORT.md`: "Residual Relationship Identity Gap: The verifier currently receives the RG-02 semantic status flag rather than an explicit canonicalized relationship identity. True canonical structural matching remains an identified gap."
**Interpretation:** Recent audits accurately recognized this as a gap, but architectural design specs do not specify the structure.

## 5. Search Query: Poisoning / Entity Misattribution
**Command:** `git grep -n -i "poisoning" -- "reports/security/*.md" "reports/research/*.md"`
**Hits:** High
**Relevant Sections:**
- `reports/security/retrieval_poisoning_evaluation.md`: "Entity Misattribution | Compound A safety profile assigned to Compound B"
**Interpretation:** Security specs explicitly require defense against entity misattribution.
