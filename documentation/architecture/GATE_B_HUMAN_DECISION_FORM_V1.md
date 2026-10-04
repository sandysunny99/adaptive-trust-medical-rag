# GATE B HUMAN DECISION FORM

**Instructions:** The research owner must complete this form to resolve the open methodological questions. Do not proceed to Gate C without authorization.

---

## DECISION 1: Trust Missing-Value Policy

The variables `query_relevance` and `evidence_quality` default to `0.0`. Under the current weights, this renders Risk Tier R3 mathematically impassable.

[ ] **OPTION A:** Impute missing values from existing signals (e.g., retrieval scores).
[ ] **OPTION B:** Exclude missing factors from the formula and mathematically renormalize the remaining weights.
[ ] **OPTION C:** Keep current behavior (0.0 defaults) and formally document R3 as impassable.

**Researcher's reasoning:**
________________________________________________________________________________
________________________________________________________________________________

**Conditions:**
________________________________________________________________________________
________________________________________________________________________________

---

## DECISION 2: Anti-Injection Representation

The variable `anti_injection` is currently set to a constant `1.0`. It provides no discriminative value in the continuous trust score, as prompt injection is evaluated as a hard boolean gate downstream.

[ ] **KEEP CONSTANT STRUCTURAL VALUE** (Accept the constant bonus to preserve the denominator).
[ ] **REMOVE FROM CONTINUOUS TRUST / HARD GATE ONLY** (Exclude and renormalize remaining weights).
[ ] **OTHER RESEARCH-DEFINED APPROACH** (Define below).

**Researcher's reasoning:**
________________________________________________________________________________
________________________________________________________________________________

**Conditions:**
________________________________________________________________________________
________________________________________________________________________________

---

**Authorized by:** ________________________  
**Date:** ________________________  
**Action:** Upon signature, apply authorized code/config changes, generate Architecture Freeze Certificate, and transition to GATE C.
