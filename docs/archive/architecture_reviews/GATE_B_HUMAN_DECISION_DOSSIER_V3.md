# GATE B HUMAN DECISION DOSSIER V3

**Date:** 2026-10-03  
**Stage:** GATE B (Architecture Freeze)  
**Status:** BLOCKED ON HUMAN DECISION

---

## 1. CURRENT VERIFIED SYSTEM STATE
- **GATE A:** COMPLETE
- **GATE B:** BLOCKED ON HUMAN DECISION
- **GATE C:** BLOCKED (No LLM Provider Credential)
- **Security Validation:** `INTEGRATION_TESTED` / `OFFLINE_EXECUTED` (No live LLM exists for Generative E2E yet).

## 2. TRUST FORMULA RECONSTRUCTION
- **R0 Max:** `0.70` (Reachable, threshold `0.30`)
- **R1 Max:** `0.65` (Reachable, threshold `0.45`)
- **R2 Max:** `0.65` (Reachable, threshold `0.60`)
- **R3 Max:** `0.65` (**IMPASSABLE**, threshold `0.75`)
- *Calculation assumes `query_relevance=0.0` and `evidence_quality=0.0`, with all other populated factors at `1.0`.*

## 3. HISTORICAL GATE 5 IMPACT
- **Factually Established:** Trust scores were systematically depressed by `0.30 - 0.35`.
- **Unknown (Requires Query Log Audit):** It is highly likely Gate 5 evaluated standard pharmacological queries (R1/R2) where the ceiling did not cause false rejections. If R3 queries were present, they were unconditionally rejected.

## 4. ANTI-INJECTION SEMANTIC MODEL
- **Execution Order:** Trust is calculated *before* Prompt Injection Detection.
- **Consequence:** `anti_injection=1.0` is a constant structural placeholder. It provides zero continuous discriminative security value, relying entirely on the downstream hard-gate detector. 

## 5. TRUST OPTION A (Impute)
- **Proposal:** Impute `query_relevance` from retrieval scores (e.g., BM25 / Cosine).
- **Methodology Impact:** **CRITICAL CIRCULARITY.** Trust eligibility becomes bound to the retrieval engine's scaling math. This confounds the core Baseline vs Cognee comparability experiment.

## 6. TRUST OPTION B (Renormalize)
- **Proposal:** Exclude the two missing factors; scale remaining 7 weights to 1.0.
- **Methodology Impact:** Formally alters the 9-factor model into a 7-factor model. Changes threshold semantics (e.g., `authority` weight spikes). Breaks Gate 5 comparability entirely.

## 7. TRUST OPTION C (Keep 0.0)
- **Proposal:** Keep current defaults (Missing = Zero).
- **Methodology Impact:** Acts as a fail-closed measurement deficiency penalty. Preserves Gate 5 exactly. Permanently locks out R3 unless instrumentation is added.

## 8. ANTI-INJECTION OPTIONS
- **A (Keep 1.0):** Mathematically preserves Gate 5 (since `poisoning_score=0.0` in safe baseline corpus). Semantically flawed as a placeholder.
- **B (Remove/Renormalize):** Fixes semantic model (hard-gate only) but breaks Gate 5 denominator.

## 9. 3×3 DEPENDENCY MATRIX
Only ONE combination (**Trust Option C + Anti-Inject Option A**) preserves the mathematical denominator, avoiding a massive baseline rerun.

## 10. RERUN REQUIREMENTS
If Trust Option A/B or Anti-Inject Option B/C is chosen, the entire 92-run Gate 5 Offline Baseline Benchmark MUST be re-executed to establish a valid comparative baseline for Cognee.

## 11. METHODOLOGY IMPACT
The normative protocol is explicitly silent on missing-value fallback rules. The 0.0 defaults are a `dataclass` artifact acting as a de-facto fail-closed safety rule.

## 12. UNKNOWN INFORMATION
Did the Gate 5 benchmark actually contain R3 (High Risk/Lethal) queries? (Requires manual query log audit).

## 13. HUMAN DECISIONS REQUIRED
1. Trust Missing-Value Policy (A/B/C)
2. Anti-Injection Representation (A/B/C)

## 14. POST-DECISION EXECUTION PATH
Human Decision → Minimal Code Change → Deterministic Tests → Gate B Architecture Freeze → Gate C (Live Provider Credential).
