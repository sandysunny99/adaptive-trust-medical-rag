# Final Cross-Repository Gap Audit

> [!NOTE]
> This audit compares 7 external repositories against the current Adaptive Trust Medical RAG codebase.
> External repositories are treated as **capability sources**, not architectural replacements.
> Phase 15 remains frozen and untouched.

## Audit Date: 2026-09-16

---

## 1. volcengine/OpenViking

| Field | Value |
|---|---|
| **SOURCE** | volcengine/OpenViking |
| **CAPABILITY CONSIDERED** | L0/L1/L2 context layering, resource hierarchy, session-to-memory workflow, context retrieval planning |
| **CURRENT PROJECT EQUIVALENT** | `context_engine/` — `ContextLevel(L0/L1/L2)`, `ContextStore`, `ResourceManager`, `RetrievalTrace`, `SessionContext` |
| **ALREADY INTEGRATED?** | YES — L0/L1/L2 enum and progressive retrieval via `load_level()` |
| **USEFUL REMAINING GAP** | Automated L0/L1 synthesis from L2 text; token window budget management |
| **RECOMMENDED ACTION** | (B) Add `ContextMetadata` dataclass with token estimates per level |
| **SCIENTIFIC IMPORTANCE** | MEDIUM — improves context efficiency but does not change core trust/safety research |
| **ENGINEERING IMPORTANCE** | MEDIUM — useful for production deployment |

**Assessment:** The L0/L1/L2 layering is **already implemented** in `ContextLevel` enum with progressive retrieval. OpenViking's session-to-memory workflow is conceptually present in `SessionContext` → `SessionMemory`. The main remaining gap is automated L0/L1 compression from raw L2 text, which is a runtime optimization, not a research-blocking gap.

---

## 2. rohitg00/agentmemory

| Field | Value |
|---|---|
| **SOURCE** | rohitg00/agentmemory |
| **CAPABILITY CONSIDERED** | Persistent memory lifecycle, governance, provenance/versioning, session continuity |
| **CURRENT PROJECT EQUIVALENT** | `research_memory/` — `MemoryStore`, `SessionMemory`, `ExperimentMemory`, `DecisionMemory`, `FailureMemory` |
| **ALREADY INTEGRATED?** | PARTIALLY — provenance enforcement exists (`MemoryRecord.__post_init__`), 4 memory types, deep-copy isolation |
| **USEFUL REMAINING GAP** | Memory versioning/revision tracking; hot/warm/cold lifecycle states |
| **RECOMMENDED ACTION** | (B) Add `version`, `schema_version`, `lifecycle_state` fields to `MemoryRecord` |
| **SCIENTIFIC IMPORTANCE** | LOW — memory versioning does not affect Phase 15 results |
| **ENGINEERING IMPORTANCE** | MEDIUM — important for long-running experiment auditability |

**Assessment:** The `research_memory/` module already enforces provenance with `source`/`origin`/`reference` validation and deep-copy isolation. agentmemory's TypeScript stack should NOT replace the Python implementation. The useful adaptation is adding version metadata and lifecycle state (`ACTIVE`/`ARCHIVED`/`SUPERSEDED`) to `MemoryRecord`.

---

## 3. K-Dense-AI/scientific-agent-skills

| Field | Value |
|---|---|
| **SOURCE** | K-Dense-AI/scientific-agent-skills |
| **CAPABILITY CONSIDERED** | Pharmacology/medicine scientific skills, literature search, evidence analysis, reproducibility |
| **CURRENT PROJECT EQUIVALENT** | `skills/` — 9 registered Python skills + 8 agent markdown skills |
| **ALREADY INTEGRATED?** | YES — all pharmacology-relevant skills are implemented as domain-specific wrappers |
| **USEFUL REMAINING GAP** | Skill metadata enrichment (security classification, evidence requirements, input/output typing) |
| **RECOMMENDED ACTION** | (B) Add `SkillMetadata` to `registry.json` entries with `security_classification`, `evidence_required`, `risk_tier` |
| **SCIENTIFIC IMPORTANCE** | LOW — skill metadata does not change experimental outcomes |
| **ENGINEERING IMPORTANCE** | MEDIUM — improves reproducibility documentation |

**Assessment:** The 9-skill pharmacology registry is complete and covers the research scope. The scientific-agent-skills repo has 165+ skills across broad scientific domains — importing them would add irrelevant complexity. The useful enhancement is enriching skill registry entries with typed contracts and security classifications.

**Current Skill Registry:**

| # | Skill | Status |
|---|---|---|
| 01 | Drug Entity Resolution | ✅ Implemented |
| 02 | Pharmacology Query | ✅ Implemented |
| 03 | Literature Retrieval | ✅ Implemented |
| 04 | Source Validation | ✅ Implemented |
| 05 | Trust Analysis | ✅ Implemented |
| 06 | Claim Verification | ✅ Implemented |
| 07 | Contradiction Analysis | ✅ Implemented |
| 08 | Abstention | ✅ Implemented |
| 09 | Experiment Analysis | ✅ Implemented |

---

## 4. mukul975/Anthropic-Cybersecurity-Skills

| Field | Value |
|---|---|
| **SOURCE** | mukul975/Anthropic-Cybersecurity-Skills |
| **CAPABILITY CONSIDERED** | MITRE ATLAS, NIST AI RMF, ATT&CK, D3FEND, security skill/test mappings |
| **CURRENT PROJECT EQUIVALENT** | `security/` + `security_extensions/` + `security_evaluation/` — sanitizer, injection detector, poisoning detector, boundary enforcer, security cases |
| **ALREADY INTEGRATED?** | PARTIALLY — security controls exist but lack formal framework mappings |
| **USEFUL REMAINING GAP** | MITRE ATLAS technique IDs and NIST AI RMF control mappings for existing security controls |
| **RECOMMENDED ACTION** | (B) Add `SECURITY_FRAMEWORK_MAPPING.md` mapping existing controls to ATLAS/NIST |
| **SCIENTIFIC IMPORTANCE** | MEDIUM — strengthens thesis security claims with recognized framework vocabulary |
| **ENGINEERING IMPORTANCE** | LOW — documentation enhancement only |

**Assessment:** The security engine is functionally complete with prompt injection detection, retrieval poisoning detection, boundary enforcement, and a formal security evaluation framework. The gap is purely **taxonomic** — no MITRE ATLAS technique IDs or NIST AI RMF control references appear anywhere in code or documentation. Adding a mapping document would let the thesis reference recognized industry frameworks without rebuilding the security engine.

**Recommended Mappings (selected, not all 817):**

| Existing Control | MITRE ATLAS | NIST AI RMF |
|---|---|---|
| `PromptInjectionDetector` | AML.T0051 (LLM Prompt Injection) | MANAGE 2.3 |
| `RetrievalPoisoningDetector` | AML.T0043 (Data Poisoning) | MAP 3.4 |
| `AuthorizationBoundary` | AML.T0054 (LLM Jailbreak) | GOVERN 1.2 |
| `InputSanitizer` | AML.T0051.001 (Direct Injection) | MANAGE 2.2 |
| `EvidenceEligibilityGate` | AML.T0048 (Model Evasion) | MEASURE 2.6 |
| `ToolExecutor` | AML.T0040 (ML Supply Chain) | GOVERN 1.5 |

---

## 5. ai-boost/awesome-harness-engineering

| Field | Value |
|---|---|
| **SOURCE** | ai-boost/awesome-harness-engineering |
| **CAPABILITY CONSIDERED** | Checkpoints, run state, context delivery, verification, observability, human approval |
| **CURRENT PROJECT EQUIVALENT** | `research_harness/` — `GateEngine`, `RunManifest`, `ArtifactRegistry`, `ApprovalManager`, `FailureTaxonomy` |
| **ALREADY INTEGRATED?** | PARTIALLY — gates, manifests, approvals, and artifact integrity exist |
| **USEFUL REMAINING GAP** | Run-state machine; checkpoint/resume for long experiments |
| **RECOMMENDED ACTION** | (B) Add `RunState` enum and `ExperimentCheckpoint` dataclass to research_harness |
| **SCIENTIFIC IMPORTANCE** | HIGH — directly enables reliable Phase 15 execution (200 cases) |
| **ENGINEERING IMPORTANCE** | HIGH — prevents data loss from interrupted long runs |

**Assessment:** The research harness has strong foundations (gates, manifests, SHA-256 artifact integrity, human approval workflow) but lacks two critical capabilities for Phase 15:

1. **Run-state machine**: No formal lifecycle tracking (`DESIGNED` → `FROZEN` → `AUTHORIZED` → `RUNNING` → `COMPLETED` → `ANALYZED`)
2. **Checkpoint/resume**: If Phase 15 is interrupted at case 150/200, there is no mechanism to resume from the last completed case

---

## 6. cathrynlavery/diagram-design

| Field | Value |
|---|---|
| **SOURCE** | cathrynlavery/diagram-design |
| **CAPABILITY CONSIDERED** | Architecture, sequence, data-flow, state diagrams for documentation |
| **CURRENT PROJECT EQUIVALENT** | Mermaid diagrams in markdown artifacts |
| **ALREADY INTEGRATED?** | NO — not a runtime dependency; documentation tool only |
| **USEFUL REMAINING GAP** | Publication-grade SVG architecture diagrams for thesis/PPT |
| **RECOMMENDED ACTION** | (D) Use diagram patterns for final thesis documentation only |
| **SCIENTIFIC IMPORTANCE** | NONE — purely presentational |
| **ENGINEERING IMPORTANCE** | NONE — documentation asset |

**Assessment:** Should remain a documentation/presentation resource. Not a runtime dependency.

---

## 7. public-apis/public-apis

| Field | Value |
|---|---|
| **SOURCE** | public-apis/public-apis |
| **CAPABILITY CONSIDERED** | Health/medical API discovery |
| **CURRENT PROJECT EQUIVALENT** | `evidence_sources/` — PubMed, Europe PMC, openFDA, RxNorm adapters |
| **ALREADY INTEGRATED?** | YES — authoritative pharmacology APIs are already integrated |
| **USEFUL REMAINING GAP** | None for current research scope |
| **RECOMMENDED ACTION** | (E) Unnecessary — existing source chain is complete |
| **SCIENTIFIC IMPORTANCE** | NONE |
| **ENGINEERING IMPORTANCE** | NONE |

**Assessment:** The authoritative pharmacology source chain (RxNorm, PubMed, Europe PMC, openFDA) is already implemented. The public-apis catalog should NOT be treated as a trusted evidence source.

---

## Gap Classification Summary

| Gap | Category | Source | Action |
|---|---|---|---|
| Context `ContextMetadata` with token estimates | B | OpenViking | Add dataclass |
| Memory `version`/`lifecycle_state` fields | B | agentmemory | Add to `MemoryRecord` |
| Skill `SkillMetadata` with security classification | B | scientific-agent-skills | Add to registry |
| Security framework mapping document | B | Cybersecurity-Skills | Create `SECURITY_FRAMEWORK_MAPPING.md` |
| Research harness `RunState` + `ExperimentCheckpoint` | B | awesome-harness | Add to research_harness |
| Automated L0/L1 synthesis from L2 | D | OpenViking | Future optimization |
| Memory persistence (database-backed) | D | agentmemory | Future if needed |
| Skill stub implementations → real execution | C | scientific-agent-skills | Needs Phase 15 validation |
| Dynamic Bayesian trust weighting | D | N/A | Future research |
| Diagram design patterns for thesis | D | diagram-design | Documentation only |
| Additional public APIs | E | public-apis | Unnecessary |

**Legend:**
- **A** = Already complete
- **B** = Small engineering enhancement (implement now)
- **C** = Research validation pending
- **D** = Optional/future
- **E** = Unnecessary
