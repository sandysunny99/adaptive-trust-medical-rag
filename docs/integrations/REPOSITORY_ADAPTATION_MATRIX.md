# Repository Adaptation Matrix

**Date:** 2026-09-05
**Status:** SURVEY COMPLETE

This matrix maps capabilities from the 7 surveyed repositories against the existing codebase to determine the correct adaptation strategy.

| Repository | Capability | Selected Feature | Local Module | Implementation Type | Phase Originally Relevant | Current Retrofit Status | Build Now? | Integrate Now? | Evaluate Later? | Dependencies | Tests | Research Value | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `ai-boost/awesome-harness-engineering` | Research Harness | Gate Engine, Artifact Registry, Approval State | `research_harness/` | New Isolated Module | Phase 4 | `RETROFIT_NOW` | YES | NO (isolated) | YES (Phase 21+) | None | `test_harness.py` | High (ensures reproducibility) | DEVELOPED |
| `ai-boost/awesome-harness-engineering` | Security Evaluation | Eval Infrastructure, Baseline/Hardened Parity | `security_evaluation/` | New Isolated Module | Phase 13 | `RETROFIT_NOW` | YES | NO (isolated) | NO | Research Harness | `test_security_evaluation.py` | High (ensures unbiased security metrics) | DEVELOPED (Phase 13C Dataset Candidate Generated) |
| `K-Dense-AI/scientific-agent-skills` | Skill Surface | Discoverable scientific skill architecture (`SKILL.md` wrappers) | `skills/` | Thin Wrappers | Phase 2, 3, 5, 6 | `RETROFIT_NOW` | YES | YES (safe surface) | YES (Phase 21+) | Existing Core | `test_skills.py` | High (standardized agent-facing scientific capabilities) | DEVELOPED |
| `volcengine/OpenViking` | Context Engine | L0/L1/L2, Session Context, Resource Mgmt | `context_engine/` | New Isolated Module | Phase 4 | `RETROFIT_NOW` | YES | NO (isolated) | YES (Phase 21+) | None | `test_context_engine.py` | High (token efficiency, tracing) | DEVELOPED |
| `rohitg00/agentmemory` | Research Memory | Session/Experiment/Failure Memory | `research_memory/` | New Isolated Module | Phase 4 | `RETROFIT_NOW` | YES | NO (isolated) | YES (Phase 21+) | None | `test_research_memory.py` | High (cross-run observability) | DEVELOPED |
| `rohitg00/agentmemory` | Hybrid Retrieval | BM25 + Vector + KG + RRF | `hybrid_retrieval.py` | Already Exists | Phase 3 | `REFERENCE_ONLY` | NO | N/A | N/A | N/A | N/A | Verified implementation | COMPLETE |
| `mukul975/Anthropic-Cybersecurity-Skills` | Security Extensions | Prompt Injection, Threat Model, Auth | `security_extensions/` | Extend Existing Module | Phase 6 | `RETROFIT_NOW` | YES | NO (isolated) | YES (Phase 14/15) | Existing Sanitizer | `test_security_extensions.py` | High (defensive robustness) | DEVELOPED |
| `cathrynlavery/diagram-design` | Architecture Docs | Pipeline, trust flow diagrams | `docs/architecture/` | Static Assets | Phase 1 | `RETROFIT_NOW` | YES | N/A | N/A | None | N/A | High (thesis communication) | DEVELOP |
| `public-apis/public-apis` | Source Discovery | API Endpoints (FDA, PubMed, ChEMBL) | `evidence_sources/` | Already Exists (4 APIs) | Phase 2 | `REFERENCE_ONLY` | NO | N/A | N/A | N/A | N/A | Verified implementation | COMPLETE |
| `public-apis/public-apis` | Source Expansion | New validated APIs | `evidence_sources/` | Future Module | Phase 20 | `DEFER_TO_NEXT_PHASE` | NO | NO | YES | Source Validator | TBD | Moderate (broadens corpus) | DEFER |



- **Phase 13C Human Review Infrastructure**: DEVELOPED=YES, INTEGRATED=NO, VALIDATED=NO
