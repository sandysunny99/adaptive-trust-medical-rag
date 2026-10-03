# Canonical Relationship Identity Specification Audit

## Implicit Requirements Found
1. **AGENTS.md (Rule 2.3):** "Never attribute evidence about Drug A to Drug B, or conflate different formulations/salts/routes of administration." - This requires explicit identity binding, which textual NLI cannot robustly guarantee.
2. **rag_orchestrator.py:** Step 2 is explicitly labeled "Drug Entity Normalization (RxCUI resolution)", proving the intent was to use RxCUIs in the pipeline.
3. **trust_scorer.py:** References an "RxCUI / entity alignment score", implying canonical identities should be used to weigh evidence trust.

## Actual Specification Status
**SPECIFICATION_GAP**
The research architecture implicitly depends on canonical identity propagation to prevent entity conflation and relationship hallucination, but no explicit data structures (`CanonicalRelationshipIdentity`) or comparison algorithms are defined in the current architecture or interfaces.
