# Feature Retrofit Register

**Date:** 2026-09-05
**Status:** SURVEY COMPLETE

This register documents capabilities that should logically have been included in earlier phases, their current status, and the safe retrofit action.

| Feature | Original Intended Phase | Current Phase | Why Missed | Affects Historical Exp? | Retrofit Action | Future Integration Phase | Evaluation Required | Status |
|---|---|---|---|---|---|---|---|---|
| **Gate Engine** | Phase 4 (Reproducibility) | Phase 5 (Annotation) | Built ad-hoc scripts instead of programmatic class | NO | Build `GateEngine` as isolated component in `research_harness/`. Do not rewrite 2F.5A or 2F.5B gate scripts. | Phase 21 (Integrated Agent) | YES (Unit) | `RETROFIT_NOW` (DEVELOPED) |
| **Artifact Registry** | Phase 4 (Reproducibility) | Phase 5 (Annotation) | Relied on JSON manifest logs without lookup API | NO | Build `ArtifactRegistry` in `research_harness/`. Do not rebuild canonical manifest. | Phase 21 (Integrated Agent) | YES (Unit) | `RETROFIT_NOW` (DEVELOPED) |
| **Approval Manager** | Phase 4 (Reproducibility) | Phase 5 (Annotation) | Approval recorded in user chat context only | NO | Build `ApprovalManager` in `research_harness/`. | Phase 7 (Confirmation) | YES (Unit) | `RETROFIT_NOW` (DEVELOPED) |
| **Skill Surface (SKILL.md)** | Phase 2, 3, 5, 6 | Phase 5 (Annotation) | Capabilities built as deep Python modules without agent interfaces | NO | Create thin wrappers in `skills/` for existing modules (`DrugNormalizer`, etc.) | Phase 21 (Integrated Agent) | YES (Unit) | `RETROFIT_NOW` (DEVELOPED) |
| **Hierarchical Context Engine** | Phase 4 (Retrieval) | Phase 10 (Context Engine) | Token truncation managed implicitly in orchestrator | NO | Build isolated `context_engine/` (ContextStore, ResourceManager, RetrievalTrace, SessionContext). | Phase 21 (Integrated Agent) | YES (Unit) | `RETROFIT_NOW` (DEVELOPED) |
| **Session Memory** | Phase 4 (Retrieval) | Phase 11 (Research Memory) | State existed only in memory during script execution | NO | Build `research_memory/` (SessionMemory, ExperimentMemory, etc.) in isolation. | Phase 21 (Integrated Agent) | YES (Unit) | `RETROFIT_NOW` (DEVELOPED) |
| **Threat Model Documentation** | Phase 1 (Architecture) | Phase 12 (Security Extensions) | Rules written, but formal model missing | NO | Document threat model in `security_extensions/` and markdown. | N/A | YES (Unit) | `RETROFIT_NOW` (DEVELOPED) |
| **Failure Taxonomy** | Phase 4 (Reproducibility) | Phase 5 (Annotation) | Ad-hoc text descriptions | NO | Build `FailureTaxonomy` in `research_harness/`. | Phase 21 (Integrated Agent) | YES (Unit) | `RETROFIT_NOW` (DEVELOPED) |
| **Run Manifest** | Phase 4 (Reproducibility) | Phase 5 (Annotation) | Ad-hoc JSON dicts | NO | Build `RunManifest` in `research_harness/`. | Phase 21 (Integrated Agent) | YES (Unit) | `RETROFIT_NOW` (DEVELOPED) |
| **Security Evaluation Harness** | Phase 4 (Reproducibility) | Phase 13 (Security Evaluation) | No evaluation infrastructure for security | NO | Build `security_evaluation/` using Research Harness adapters | Phase 14 (Evaluation) | YES (Unit) | `RETROFIT_NOW` (DEVELOPED - Phase 13B Design Complete) |


- **Phase 13C Human Review Infrastructure**: DEVELOPED=YES, INTEGRATED=NO, VALIDATED=NO
