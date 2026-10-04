# SimpleEmbeddingModel Authorization Audit

## Introduction
*   **Commit:** `ea9735570ff7e40e6e03e441df6b59dcd4ab05f2`
*   **Date:** 2026-08-23 14:20:01 +0530
*   **Purpose:** "replace mock ablation engine with real live Medical RAG execution pipeline"

## Analysis of Stated Purpose
The commit message clearly states the purpose was to transition the project from a "mock ablation engine" to a live pipeline. However, to satisfy type constraints for the new live pipeline while building it, several temporary mocks were introduced, including `SimpleLLMBackend` and `SimpleEmbeddingModel`. 

This is evident from the model's design:
- It returns 7-dimensional vectors.
- It only recognizes exactly 7 hardcoded tokens (`metformin`, `aspirin`, `warfarin`, `dosage`, `mechanism`, `renal`, `indication`).
- Any query lacking these tokens receives a 100% zero-vector.

## Promotion into Architecture Snapshot
*   **Commit:** `b18461df0f96d45fc2e8378c005e2f872f3e792e`
*   **Date:** 2026-09-13 00:23:41 +0530
*   **Document:** `CURRENT_ARCHITECTURE_SNAPSHOT.md`

`CURRENT_ARCHITECTURE_SNAPSHOT.md` was created to document the codebase state for Phase 14.5 guardrail evaluations. It listed `SimpleEmbeddingModel` simply because that was the class instantiated by `rag_orchestrator.py` at the time.

This document is **DESCRIPTIVE** (capturing current state), not **NORMATIVE** (prescribing the intended research protocol).

## Conclusion
`SimpleEmbeddingModel` is a temporary testing fixture. It was never intended to serve as a production or research-evaluation baseline. It received no formal protocol authorization and was only documented in the architecture snapshot due to an accidental artifact of the descriptive documentation process.

`evidence_source`: `manual_analysis`
