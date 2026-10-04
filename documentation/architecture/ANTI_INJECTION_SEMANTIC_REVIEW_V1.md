# ANTI-INJECTION SEMANTIC REVIEW

**Date:** 2026-10-03  
**Stage:** GATE B (Architecture Freeze)

## 1. Trace

**Pipeline Execution Order:**
1. **Scoring:** `HybridRetrievalEngine` returns `Candidate`.
2. **Trust Construction:** `rag_orchestrator.py` L502-510 builds `TrustFactorScores`.
3. **Trust Formula:** `AdaptiveTrustScorer` applies risk-tier weights.
4. **Hard Security Gate:** `EvidenceEligibilityGate` calls `PromptInjectionDetector.inspect(cand.text)` (L540).

## 2. Forensic Semantic Analysis

The previous correction set `anti_injection=1.0` in the `TrustFactorScores` constructor (L508) because the original assignment (`1.0 - cand.poisoning_score`) was a copy-paste error that conflated retrieval poisoning with prompt injection. 

However, we must challenge if setting a **constant `1.0`** is semantically correct for the trust formula.

- **Does `anti_injection` participate materially in the trust formula?** Yes. Its weights are R0(0.05), R1(0.05), R2(0.02), R3(0.01).
- **Does setting it permanently to 1.0 create a semantic mismatch?** Yes. A constant term provides exactly zero discriminative value across different candidate chunks. It mathematically functions as a free +0.01 to +0.05 bonus point applied uniformly to all chunks.
- **Is there an execution ordering problem?** Yes. The trust score is calculated *before* the `PromptInjectionDetector` inspects the candidate text. Therefore, the trust formula cannot know if the chunk is injected at the time it calculates the score.
- **Can a poisoned/suspicious candidate receive full trust?** A chunk containing malicious prompt injection will receive `anti_injection = 1.0` during scoring. It will be correctly caught and rejected by the hard downstream detector later, but its *recorded trust score* will falsely reflect maximum injection safety.

## 3. Classification

**Classification:** `SEMANTICALLY_INCORRECT` / `REQUIRES_EXCLUSION_FROM_TRUST_FORMULA`

The variable `anti_injection` inside `TrustFactorScores` acts as a structural placeholder for a signal that was intended to be continuous but is actually implemented as a binary hard-gate later in the pipeline.

**Conclusion:** Setting `anti_injection = 1.0` is a valid *structural workaround* that allows the mathematical formula to execute without crashing or falsely penalizing based on poisoning scores. However, it is *semantically incorrect* because it represents an unmeasured signal. 

This issue is inherently linked to the 9-factor model design and should be resolved as part of the overall Trust Policy research decision.
