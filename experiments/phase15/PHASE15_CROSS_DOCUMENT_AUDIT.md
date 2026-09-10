# Phase 15 Cross-Document Audit

**Date:** 2026-09-08
**Status:** Audit Complete

## Cross-Document Consistency Check

| Area | Status | Notes |
|------|--------|-------|
| Evaluation Scope | CONSISTENT | All docs refer to orchestrator-level execution. |
| Baseline | CONSISTENT | Defined as standard semantic RAG with security gates bypassed. |
| Hardened System | CONSISTENT | Defined as the Phase 14 integrated architecture. |
| Experimental Unit | CONSISTENT | Paired observation (same query, corpus, seeds). |
| Scenario Families | CONSISTENT | 6 families defined in Protocol. |
| Primary Endpoint | CONSISTENT | Security Failure Rate (SFR) across documents. |
| Secondary Endpoints | CONSISTENT | Task Utility, Unnecessary Abstention, Latency. |
| Outcome Taxonomy | REQUIRES CLARIFICATION | `PHASE15_METRIC_DEFINITIONS.md` uses 8 categorical states. `PHASE15_FAILURE_TAXONOMY.md` uses F1-F12. A direct mapping must be enforced (e.g., `UNSUPPORTED_OUTPUT` maps to F6/F7). |
| Sample Size | CONSISTENT | N=200 recommended across docs. |
| Statistical Test | CONSISTENT | McNemar's exact test for paired binary data. |
| Confidence Intervals | CONSISTENT | Exact 95% CIs for paired proportions. |
| Annotation Procedure | CONSISTENT | Blinded human review for correctness/support. |
| Reproducibility | CONSISTENT | Fixed seeds, temperature 0.0, isolated processes. |

## Identified Conflicts & Required Corrections

**Conflict 1: Outcome vs. Failure Taxonomy**
- **Document:** `PHASE15_METRIC_DEFINITIONS.md` vs `PHASE15_FAILURE_TAXONOMY.md`
- **Conflict:** The metric definitions document uses 8 outcome labels (e.g., `POISONED_EVIDENCE_USED`), while the failure taxonomy uses 12 specific root-cause tags (e.g., `F2 - Poisoned Evidence Accepted`).
- **Required Correction:** Ensure that the 8 Outcome Taxonomy labels serve as the *Primary Endpoint Classification* (mutually exclusive), and the F1-F12 tags serve as *Secondary Annotations* (can be multiple) to avoid double-counting in SFR.
- **Scientific Consequence:** Prevents statistical inflation of failure rates if one case exhibits multiple failure modes (e.g., F6 and F7).

**Conflict 2: Baseline "Bypassed" Meaning**
- **Document:** `PHASE15_BASELINE_SPEC.md`
- **Conflict:** Uses the term "security gates bypassed". 
- **Required Correction:** Must explicitly state that this means *bypassing enforcement* (e.g., hardcoded to return `ALLOW` or `True`) rather than removing the components from the codebase, to maintain matching execution graphs where possible without artificially reducing baseline latency.
- **Scientific Consequence:** Ensures latency overhead (TLO) measures the cost of *computation* rather than just branching.
