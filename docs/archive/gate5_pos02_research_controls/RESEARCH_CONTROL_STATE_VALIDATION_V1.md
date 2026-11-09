# Research Control State Validation (V1)

**Timestamp:** 2026-10-04T23:33:00Z
**Validation Version:** 1.0

This document tracks the current validation state of the research controls prior to authorizing the V1.2 formal 160-request experiment.

| Control | Status | Source of Truth | Validation Method | Artifact | Hash/Version | Browser State | Notes |
|---------|--------|----------------|-------------------|----------|--------------|---------------|-------|
| **Dataset Integrity** | PASS | File system & Hash | SHA256 check & case count | `experiments/manifests/v3_1_human_cases.json` | `db4013a9...` | PASS | |
| **Case Order Integrity** | PASS | File system array | Unique case_id check | `experiments/manifests/v3_1_human_cases.json` | `bb47d3c1...` | PASS | |
| **Frozen Retrieval** | PASS | V1.2 Protocol manifest | JSON parsing of artifact_identity | `REAL_LLM_EVALUATION_PROTOCOL_V1_2.json` | N/A | PASS | Requires FROZEN_HISTORICAL_OUTPUT |
| **Trust/Evidence Control** | VALIDATED | `RESEARCH_READINESS_MANIFEST_V1.json` | Static manifest parsing | `trust_scorer.py` | N/A | VALIDATED | Historical validation |
| **Claim Verification** | VALIDATED | `RESEARCH_READINESS_MANIFEST_V1.json` | Static manifest parsing | `claim_verifier_v2.py` | N/A | VALIDATED | Verified semantic judgments |
| **Controlled Abstention** | VALIDATED | `RESEARCH_READINESS_MANIFEST_V1.json` | Static manifest parsing | `rag_orchestrator.py` | N/A | VALIDATED | Verified against 12 microcases |
| **Prompt Freeze** | PASS | File system & Hash | SHA256 check | `experiments/prompts/REAL_LLM_EVALUATION_PROMPT_V1_2.txt` | `e5aeb4fa...` | PASS | Must precisely match frozen state |
| **Provider Readiness** | NOT_CONFIGURED | Environment variables | os.environ check for GROQ_API_KEY | N/A | N/A | NOT_CONFIGURED | Connectivity & exact model untested |
| **Researcher Authorization**| PENDING | Pre-flight validation gates | Dependent on all other checks | N/A | N/A | PENDING | Blocked until Provider Readiness is READY |
| **Real-LLM Evaluation** | NOT_STARTED | Execution directory | Absence of executed logs | `experiments/runs/real-llm-v1_2/` | N/A | NOT_STARTED | |
