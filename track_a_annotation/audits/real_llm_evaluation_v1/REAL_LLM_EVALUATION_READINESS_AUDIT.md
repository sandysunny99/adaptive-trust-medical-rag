# Real-LLM Evaluation Readiness Audit

## A. Existing Evaluation Harness
- The repository contains src/adaptive_trust_medical_rag/evaluation/evaluator.py, experiment_tracker.py, and live_variants.py.
- LiveModelAdapter and SyncLLMBackendAdapter successfully connect the pipeline to the provider.

## B. Existing Experiment/Case Manifests
- 	rack_a_annotation/manifests/TRACK_A_RESERVED_POSITIONS.json (530 cases, LOCKED)
- experiments/manifests/v3_1_human_cases.json (80 medical evaluation cases)
- experiments/manifests/smoke_v1.json (synthetic smoke dataset)
- experiments/security_evaluation/security_cases_v2_reviewed.jsonl (security cases)

## C. Authorized Inputs
- Currently, NO explicitly authorized dataset is defined for **real-LLM** evaluation. The 530-case benchmark is locked. The 80-case 3_1_human_cases.json exists but requires protocol authorization.

## D. Existing Comparison Arms
- None defined specifically for Real-LLM Evaluation V1. Needs formal authorization (e.g., Baseline vs. Adaptive Trust).

## E. Expected Output Structure
- Standard metrics: Claim support rate, citation validation, abstention correctness, hallucination rate, and failure rate.
- JSONL format capturing full ModelGenerationResult, timings, provenance, and claims.

## F/G. Formally Authorized Metrics
- Retrieval metrics (frozen).
- Generation metrics require definition (e.g., citation support rate, contradiction rate, unsupported rate).

## H. Frozen/Protected Experiments
- Track A (530/530 cases)
- Historical BM25/Dense retrieval
- Gate 5 evidence processing
- Trust P0 V2
- Claim-Evidence Remediation V1
- Controlled Abstention V1
- Canonical Relationship Identity V1
- Phase 15 (Gemini frozen)

## I/J/K/L. Prerequisites
- **Dataset**: MISSING. A dedicated Real-LLM Evaluation manifest must be frozen.
- **Prompts**: Defined via RAGOrchestrator but must be hashed/frozen.
- **Orchestrator**: Ready. Handles sync provider bridge cleanly.

## Conclusion & Blockers
**STATUS: BLOCKED**
The repository lacks a formally frozen dataset, explicit comparison arms, and protocol definition for the real-LLM experiment. Before execution, the project must freeze an evaluation protocol and manifest to protect the research evidence chain.
