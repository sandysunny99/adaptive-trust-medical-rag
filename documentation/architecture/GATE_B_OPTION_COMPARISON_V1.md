# GATE B OPTION COMPARISON

**Date:** 2026-10-03  
**Stage:** GATE_B  

## 1. TRUST OPTION A1 (Direct Retrieval Imputation)
- **What it is:** Using the retriever's score (BM25, Cosine) for `query_relevance`.
- **What it solves:** Bypasses the 0.0 missing value to restore R3 reachability.
- **Evidence supporting:** Makes formula mathematically 100% active.
- **Evidence not supporting:** Highly circular. BM25 and vector math scale differently, meaning the trust eligibility boundary will shift depending on the retrieval engine, fatally confounding the comparative evaluation.
- **Semantics:** Redefines Trust to include "retrieval engine confidence".
- **Historical Impact:** Invalidates Gate 5 numerical scores.
- **Rerun Requirement:** MANDATORY.

## 2. TRUST OPTION A2 (Independent Relevance Imputation)
- **What it is:** Using a post-retrieval cross-encoder (MedCPT) or LLM evaluator to score relevance independently.
- **Scientific Validity:** High. Cleanly separates retrieval from relevance verification.
- **Reproducibility / Historical Impact:** Invalidates Gate 5 numerical scores.
- **Implementation Burden:** High. Requires integrating a new evaluation module not present in the Gate 5 frozen code.
- **Rerun Requirement:** MANDATORY.

## 3. TRUST OPTION B (Renormalization)
- **What it preserves:** Nothing numerical. Preserves the "continuous probability" intent by ignoring missing factors entirely.
- **What it changes:** Mathematical denominator (e.g., drops to 0.65). Relative weight of `authority` jumps significantly. 
- **What it proves:** Proves that missing factors can be excised, but shifts the model to a 7-factor architecture.
- **Implementation Behavior or Normative Design:** Proposed Methodology (New Design).
- **Rerun Requirement:** MANDATORY.
- **Historical Interpretation:** Renders the 9-factor Gate 5 completely incomparable.

## 4. TRUST OPTION C (Keep Missing=0.0)
- **What it is:** Observed implementation behavior. The dataclasses default to `0.0`.
- **What it is NOT:** It is NOT a proven "normative design". The protocol does not explicitly dictate `MISSING=0.0` as a fail-closed safety rule. It is a pragmatic measurement deficiency.
- **Experimental Behavior:** Depresses scores by 30-35%.
- **Historical Impact:** PERFECT NUMERICAL EQUIVALENCE to Gate 5.
- **Rerun Requirement:** NOT REQUIRED.

## 5. ANTI-INJECTION OPTIONS
- **HISTORICAL DIFFERENCE = 0:** This means **NUMERICAL EQUIVALENCE**. For the clean frozen corpus, `1.0 - 0.0` and `1.0` produced identical outputs. It does *not* mean identical semantics (one was a calculation, one is a constant) or identical security behavior (for malicious chunks).
- **Opt A (Keep 1.0):** Preserves numerical equivalence. Semantically empty placeholder.
- **Opt B (Hard Gate Only):** Cleans up semantics (removes injection from continuous trust). Methodologically different. Denominator shrinks. Requires mandatory rerun.
- **Opt C (Continuous):** Redefines security behavior. Requires mandatory rerun.
