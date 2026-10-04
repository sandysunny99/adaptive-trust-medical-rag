# Updated Research Roadmap

> [!NOTE]
> Post-Phase 14.8 implementation-depth audit.
> Architecture-expansion cycle is **CLOSED**.
> Focus moves entirely to Track-A annotation, Gemini access, and Phase 15.

## Audit Date: 2026-09-16

---

## 1. COMPLETED (Wired, Tested, Scientifically Validated / Baselined)

| Item | Status | Evidence |
|---|---|---|
| Core RAG Pipeline | ✅ WIRED & TESTED | Complete end-to-end flow |
| RxNorm/entity resolution | ✅ WIRED & TESTED | `normalization/drug_normalizer.py` |
| Evidence sources (PubMed, Europe PMC, openFDA) | ✅ WIRED & TESTED | `evidence_sources/` adapters |
| Hybrid retrieval | ✅ WIRED & TESTED | `retrieval/` |
| Trust Engine | ✅ WIRED & TESTED | `trust_scoring/trust_scorer.py` |
| Security core | ✅ WIRED & TESTED | Custom Security Core (Phase 14) |
| Authorization/tool boundary | ✅ WIRED & TESTED | `security/agent_action.py` |
| Claim verification | ✅ WIRED & TESTED | `verification/claim_verifier.py` |
| Context engine | ✅ WIRED & TESTED | `context_engine/` |
| Memory engine | ✅ WIRED & TESTED | `research_memory/` |
| Research harness | ✅ WIRED & TESTED | `research_harness/` |
| Provider router | ✅ WIRED & TESTED | 4 providers (Groq, Gemini, Cloudflare, HF) |
| Cloudflare backend | ✅ WIRED & TESTED | Live connectivity success |

---

## 2. ENGINEERING INFRASTRUCTURE ONLY (Declared but not yet driving execution)

These Category-B capabilities were implemented for conceptual alignment and future-proofing but are **NOT** wired into the Phase 15 execution loop.

| Item | Status | Detail |
|---|---|---|
| `ContextMetadata` (L0/L1/L2 estimates) | 🟡 INFRASTRUCTURE | Declared in `ContextRecord` and `to_dict()`, but not automatically generated or consumed by retrieval token budgets. |
| Memory lifecycle/version metadata | 🟡 INFRASTRUCTURE | `version`, `schema_version`, and `lifecycle_state` exist in `MemoryRecord`, but `ACTIVE`/`ARCHIVED` states do not actively break/enable session isolation yet. |
| `SkillMetadata` | 🟡 INFRASTRUCTURE | Present in `registry.json`. Classifications (`evidence_required`, `UNCLASSIFIED`) are documented, but the skill runner does not dynamically enforce them during execution. |
| `RunState` + `ExperimentCheckpoint` | 🟡 INFRASTRUCTURE | Declared in `run_manifest.py`, but `resume()` logic is not wired into the Phase 15 execution runner. Does not alter dataset case ordering or models. |

---

## 3. EXTERNAL REPOSITORY BOUNDARIES (Documentation)

The following external repositories were used purely as conceptual capability sources, not wholesale framework replacements:

*   **OpenViking** -> Absorbed context/memory concepts only (L0/L1/L2).
*   **agentmemory** -> Absorbed memory lifecycle concepts only (versioning).
*   **scientific-agent-skills** -> Absorbed selected pharmacology/scientific skills only.
*   **Anthropic-Cybersecurity-Skills** -> Absorbed selected threat/control taxonomy only.
*   **awesome-harness-engineering** -> Absorbed harness patterns only.
*   **diagram-design** -> For documentation only.
*   **public-apis** -> For API discovery only.

---

## 4. RESEARCH VALIDATION PENDING (The Blockers)

This section represents the **true blockers** to completing the research.

| # | Blocker | Nature | Next Step |
|---|---|---|---|
| 1 | **Track A human annotation** | Scientific | Complete 530-position annotation, calculate IAA, and perform F0 vs F3 retrieval analysis. |
| 2 | **Gemini quota/access** | Runtime | Resolve quota exhaustion to unblock Phase 15. |
| 3 | **Phase 15 credentialed preflight** | Engineering | Run 1 test case with Gemini once quota is restored. |
| 4 | **Phase 15 canonical execution** | Scientific | Execute 200 baseline + 200 hardened cases with Gemini. |
| 5 | **Phase 15 statistical analysis** | Scientific | Compute SFR, McNemar's test, and confidence intervals. |
| 6 | **Final scientific interpretation** | Scientific | Contextualize results against the core research question. |

---

## Architecture Freeze Status

```
ARCHITECTURE_EXPANSION_STATUS   = CLOSED
SECURITY_PLANE                  = CUSTOM_SECURITY_CORE (canonical)
PROVIDER_ROUTING                = OPERATIONAL (Cloudflare live, Groq live)
PHASE_15                        = FROZEN / NOT STARTED
NEXT_MAJOR_WORK                 = RESEARCH VALIDATION
```
