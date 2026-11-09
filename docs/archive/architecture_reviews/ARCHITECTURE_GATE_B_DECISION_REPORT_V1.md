# ARCHITECTURE GATE B DECISION REPORT

**Date:** 2026-10-03  
**Stage:** GATE B (Architecture Freeze)  
**Status:** 🔒 BLOCKED ON HUMAN RESEARCH DECISION

This report documents the resolution of the four critical Gate B decisions identified in the Forensic Truth Audit. Three decisions have been resolved and one is explicitly escalated for human research protocol decision.

---

## DECISION 1: TRUST MISSING-VALUE POLICY (ESCALATED)

**The Issue:**
In `trust_scorer.py`, `query_relevance` and `evidence_quality` default to `0.0`. In `rag_orchestrator.py`, they are never populated. Because these two factors account for 30%-35% of the total trust weight, every candidate chunk suffers an automatic 0.30-0.35 point penalty. Under Risk Tier R3 (threshold 0.75), the maximum possible score is 0.65, making the R3 gate mathematically impassable.

**Candidate Policies:**

### Option A: Impute from formally justified existing signals
- **Interpretation:** We derive `query_relevance` from the retrieval engine (e.g., normalized RRF score or cosine similarity) and `evidence_quality` from metadata defaults (e.g., 0.8).
- **Mathematical effect:** Restores the 35% weight capacity. Maximum score returns to 1.0.
- **Effect on thresholds:** R3 (0.75) becomes passable for highly relevant, authoritative evidence.
- **Effect on historical experiments:** Changes the trust scores compared to Gate 5.
- **Implementation impact:** Requires updating L502-509 in `rag_orchestrator.py`.
- **Methodology compatibility:** Compatible with the intent of the trust formula, but requires declaring the exact imputation sources.

### Option B: Exclude and Renormalize
- **Interpretation:** If the signals cannot be computed, they are removed from the formula entirely. The remaining weights are proportionally scaled up to sum to 1.0.
- **Mathematical effect:** Max score returns to 1.0.
- **Effect on thresholds:** R3 becomes passable.
- **Effect on historical experiments:** Changes trust scores and relative weight distributions.
- **Implementation impact:** Requires rewriting `trust.yaml` or adding dynamic normalization logic to `trust_scorer.py`.
- **Methodology compatibility:** Alters the frozen 9-factor architectural blueprint.

### Option C: Keep Current Behavior (Document MISSING=ZERO)
- **Interpretation:** Accept the 0.0 default as a deliberate limitation of the current pipeline.
- **Mathematical effect:** No change. Max score remains 0.65.
- **Effect on thresholds:** R3 remains impassable. The system will aggressively abstain on high-risk queries.
- **Effect on historical experiments:** Preserves exact Gate 5 reproducibility.
- **Implementation impact:** None.
- **Methodology compatibility:** Fully compatible historically, but limits the practical utility of the R3 risk tier.

**DECISION:** 🔒 **ESCALATED TO HUMAN RESEARCHER**
We cannot silently modify the trust formula or orchestrator imputation without explicit research justification, as it alters the experimental baseline. Gate B remains OPEN pending human selection of Option A, B, or C.

---

## DECISION 2: ANTI-INJECTION SOURCE (RESOLVED)

**The Issue:** `rag_orchestrator.py` L508 incorrectly mapped `anti_injection = 1.0 - cand.poisoning_score`. This conflated retrieval poisoning (provenance) with prompt injection (instruction override).

**Resolution:**
- **Code Fixed:** L508 was updated to `anti_injection=1.0`. 
- **Justification:** Prompt injection is evaluated as a discrete, hard gate (BLOCK/FLAG/ALLOW) by the `PromptInjectionDetector` in the `EvidenceEligibilityGate`. It does not require continuous scaling in the trust formula. Setting it to 1.0 ensures no false deflation, while preserving the hard security boundary downstream.
- **Artifact:** `ANTI_INJECTION_TRACE_V1.md`

---

## DECISION 3: DYNAMIC INTEGRITY VALIDATOR (RESOLVED)

**The Issue:** `DynamicIntegrityValidator` is implemented but defaults to `None` and is unwired.

**Resolution:** 
- **Decision:** Keep OPTIONAL and UNWIRED by default.
- **Justification:** The core baseline utilizes a frozen in-memory corpus which is statically verified at load time. Enabling dynamic chunk-by-chunk verification requires a `registry_store` that the baseline does not possess. Enabling it would break Gate 5 reproducibility. 
- **Artifact:** `DYNAMIC_INTEGRITY_DECISION_V1.md`

---

## DECISION 4: RELATIONSHIP GROUNDING V2 (RESOLVED)

**The Issue:** RG-02 is unit-tested but defaults to `None` in the orchestrator.

**Resolution:**
- **Decision:** Keep OPTIONAL and UNWIRED by default.
- **Justification:** RG-02 is a pre-generation relationship filter using regex heuristics. Enabling it by default would radically alter retrieval recall and invalidate Gate 5 baseline metrics. Relationship validation remains primarily enforced post-generation via the `AnswerSafetyGate` contradiction detector.
- **Artifact:** `RG02_DEFAULT_PATH_DECISION_V1.md`
