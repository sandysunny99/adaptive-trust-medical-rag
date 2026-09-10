# Phase 15 Baseline Specification

## 1. Definition of the Baseline

The Phase 15 Baseline is a legitimate, fully functioning generative RAG system. It is specifically designed to isolate the effect of the security enforcement mechanisms without artificially degrading baseline performance.

## 2. Baseline Fairness & Comparison Boundary

Explicitly, the Baseline is **NOT**:
- A retrieval-disabled baseline.
- A generation-disabled baseline.
- A reduced-context baseline.
- A weakened model baseline.
- An artificially degraded latency baseline.

The Baseline and Hardened configurations share identical non-security parameters:
- **Same Corpus:** Frozen 200-case dataset context.
- **Same Query Set:** Exact same 200 experimental units.
- **Same Retrieval Stack:** BM25 + Vector + Graph + RRF executes fully.
- **Same Ranking Configuration:** Identical weights and top_k limits.
- **Same Generation Model:** Gemini 1.5 Pro (or equivalent locked model).
- **Same Generation Parameters:** Temperature 0.0, deterministic limits.
- **Same Context Limits:** Identical token budgets.
- **Same Prompts:** Identical system instructions, minus dynamic security enforcements.

## 3. Enforcement Bypass Mechanism

The Baseline differs from the Hardened system *only at the enforcement decision points*.
- Security computation (e.g., string matching for injection, trust scoring) may still occur, but the resulting `SecurityDecision` is universally overridden to `ALLOW`.
- `EvidenceEligibilityGate` passes all retrieved context.
- `AnswerSafetyGate` performs no post-generation suppression. 

This ensures that the latency/computation characteristics remain as close as possible to the hardened path, cleanly isolating the *security outcome* as the dependent variable.
