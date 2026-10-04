# ANTI-INJECTION EXECUTION ORDER AUDIT

**Date:** 2026-10-03  

## 1. Pipeline Execution Trace

1. **Retrieval Engine:** Yields untrusted `Candidate` document.
2. **Trust Construction:** `rag_orchestrator.py` constructs `TrustFactorScores` (including applying the constant `anti_injection=1.0`).
3. **Trust Scoring:** `AdaptiveTrustScorer` computes the continuous sum.
4. **Eligibility Threshold:** Orchestrator evaluates if `Trust >= Risk Threshold`.
5. **Security Hard Gate:** If passed, `EvidenceEligibilityGate` passes the candidate to `PromptInjectionDetector.inspect()`.
6. **Generation:** Only passed candidates enter the LLM context.

## 2. Consequences

1. **Does trust precede injection detection?** YES.
2. **Can a candidate be rejected by trust before detection?** YES.
3. **Can a candidate pass trust while containing injection?** YES. (It will receive the 1.0 bonus, clear the threshold, and proceed to the hard gate).
4. **Is the hard gate guaranteed to inspect every candidate?** YES. There is no bypass path.
5. **Is `anti_injection` ever used to make a generation decision?** NO. The generation decision is controlled exclusively by the hard downstream detector.

## 3. Audit/Logging Meaning

This execution order creates a logging defect: A malicious candidate that scores high on authority/freshness will receive the `anti_injection=1.0` bonus, pass the continuous trust gate, and then be hard-blocked. Its persisted trace logs will reflect a high trust score, falsely implying it was mathematically trusted, despite containing a malicious payload.
