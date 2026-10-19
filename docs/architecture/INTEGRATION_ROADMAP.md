# Integration Roadmap

> **Historical (2026-09-05).** This roadmap records the research-harness plan at that date. The current, evidence-backed status of every component and blocker is in [reports/audit/blocked_issue_register.md](../../reports/audit/blocked_issue_register.md); the live application is described in [docs/ARCHITECTURE.md](../ARCHITECTURE.md).

**Date:** 2026-09-05

## Phase 8: Research Harness

* **Status:** DEVELOPED
* **Components:**
  * `GateEngine`
  * `ArtifactRegistry`
  * `ApprovalManager`
  * `FailureTaxonomy`
  * `RunManifest`
* **Tests:** Passed (pytest and dedicated smoke test)
* **Integration Status:** PARTIAL (Integrated into `ExperimentTracker` for future runs. Not connected to canonical F0/F3 or Phase 2F.5B annotation gate).
* **Validation Status:** NO (Requires end-to-end evaluation in later phases).

## Next Safe Engineering Layer

**Phase 9: Skill Surface**
* Pending implementation (thin `SKILL.md` wrappers around existing modules).
