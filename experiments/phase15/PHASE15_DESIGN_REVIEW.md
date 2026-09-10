# Phase 15 Design Review

## 1. What exactly is being evaluated?
The orchestrator-level end-to-end execution path of the Adaptive Trust-Aware Medical RAG system.

## 2. What is the baseline?
A functioning semantic generative RAG pipeline with all Phase 14 security gates (injection, poisoning, eligibility, authorization, safety verification) disabled or set to pass-through.

## 3. What is the hardened system?
The fully integrated Phase 14 system with all defensive mechanisms and fail-closed gates active in the live execution path.

## 4. What is one experimental unit?
A single paired observation: one specific medical query/scenario processed independently by both the baseline and hardened systems under identical initial conditions.

## 5. What is the primary endpoint?
**Security Failure Rate (SFR)** — the proportion of queries that result in a critical security compromise (injection accepted, poisoned data utilized, unauthorized action executed, or critical ungrounded claim released).

## 6. What are the secondary endpoints?
Task Utility Rate (TUR), Unnecessary Abstention Rate (UAR-Utility), Unauthorized Action Rejection Rate (UARR), and Total Latency Overhead (TLO).

## 7. How is ground truth established?
Expert pre-annotation defining the expected security decision (Block/Abstain vs Release) and expected factual claims based on pharmacological reference standards.

## 8. How many cases are required?
Based on power analysis, **200 paired cases** are required to achieve >80% power at alpha=0.05 for detecting a 30% absolute reduction in SFR, distributed across 6 scenario families.

## 9. What statistical test will be used?
McNemar's exact test for paired nominal data.

## 10. What confidence intervals will be used?
95% exact confidence intervals for paired proportions.

## 11. What human annotation is required?
Blinded adjudication of generative outputs to assess Claim Correctness, Evidence Support, and Abstention Utility.

## 12. How is reproducibility guaranteed?
By freezing the corpus, using zero temperature for the LLM, setting deterministic random seeds, and strictly isolating the execution states of the Baseline and Hardened runs.

## 13. What are the failure categories?
A 12-point taxonomy mapping failures from Prompt Injection Bypass (F1) through Unnecessary Abstention (F10) and Latency Timeouts (F12).

## 14. What are the threats to validity?
Training/test data leakage, baseline contamination by residual security states, and over-reliance on LLM-as-judge for ground truth.

## 15. What must be frozen before execution?
Dataset, Protocol, Metric Definitions, Configurations, and Statistical Plan (per the Pre-Registration Checklist).

---

**PHASE 15 DESIGN STATUS:**
**READY FOR PROTOCOL FREEZE**
