# ANTI-INJECTION SEMANTIC DECISION DOSSIER

**Date:** 2026-10-03  
**Stage:** GATE B (Architecture Freeze)

## 1. Trace and Current State

**Pipeline Flow:**
1. Retrieval Engine yields `Candidate`.
2. Orchestrator constructs `TrustFactorScores`.
3. `anti_injection` is currently set to `1.0` (constant).
4. `AdaptiveTrustScorer` calculates continuous trust score.
5. If score > threshold, Candidate enters `EvidenceEligibilityGate`.
6. `PromptInjectionDetector.inspect(cand.text)` executes.
7. If `BLOCK` or `FLAG`, Candidate is rejected regardless of trust score.

## 2. Mathematical Impact

In the current implementation (`anti_injection = 1.0`), the system assigns the following constant bonuses to every retrieved chunk:
- **R0:** +0.10
- **R1:** +0.05
- **R2:** +0.02
- **R3:** +0.01

**Discriminative Value:** Zero. Because it is a constant, it does not differentiate between safe and unsafe chunks during the trust scoring phase.

## 3. Security Meaning

Is `anti_injection` intended as a continuous trust factor or a binary security state? 
- Prompt injection (unlike authority or freshness) is rarely a continuous spectrum. A chunk either contains adversarial instruction-override tokens or it does not.
- The architecture treats it as a discrete hard gate downstream.
- A malicious chunk receives the `1.0` bonus, passes the trust threshold, and is subsequently caught by the hard gate. No malicious chunk can bypass the detector and influence generation. However, the recorded trust score for that rejected chunk will falsely reflect "perfect" injection safety.

## 4. Possible Treatments

### A. Keep `anti_injection=1.0` structurally
- **Security meaning:** Treats the trust factor as a structural placeholder.
- **Mathematical impact:** Provides a constant bonus. Does not distort thresholds, but mathematically inflates recorded trust scores by 0.01 - 0.10.
- **Historical impact:** Safest option for maintaining Gate 5 comparability, as it stabilizes the denominator.
- **Tests/Protocol:** Requires no changes, only documentation.

### B. Remove from continuous trust / Hard gate only
- **Security meaning:** Formally acknowledges that prompt injection is a boolean security property, not a continuous trust factor.
- **Mathematical impact:** The `anti_injection` weight must be removed from `trust.yaml` and the remaining 8 weights renormalized.
- **Historical impact:** Breaks historical reproducibility. Gate 5 would need to be rerun with the new 8-factor denominator.
- **Tests/Protocol:** Requires updating the architecture document and `trust.yaml`.

### C. Redesign as a continuous signal
- **Security meaning:** Assumes the prompt injection detector can output a continuous probability score `[0, 1]` rather than just `BLOCK/FLAG/ALLOW`.
- **Mathematical impact:** Reinstates discriminative value to the factor.
- **Historical impact:** High. Requires rewriting the `PromptInjectionDetector` and rerunning Gate 5.

## 5. Conclusion

**HUMAN_DECISION_REQUIRED = YES**

The researcher must decide if the semantic impurity of a constant `1.0` placeholder is acceptable to preserve Gate 5, or if the architecture should formally exclude `anti_injection` from the continuous trust formula (Option B).
