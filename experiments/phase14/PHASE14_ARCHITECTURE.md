# Phase 14 Architecture: End-to-End RAG Security Integration

## Overview
Phase 14 transitions the adapter-level security boundary evaluated in Phase 13D into the live execution path of the Adaptive Trust-Aware Pharmacology RAG. The objective is to make the security components—PromptInjectionDetector, RetrievalPoisoningDetector, and AuthorizationBoundary—active participants in the end-to-end data flow rather than isolated simulation controls.

## End-to-End Architecture & Data Flow

`	ext
USER QUERY
    │
    ▼
API / REQUEST EDGE
    │
    ├── Prompt Injection Detection (NEW)
    ├── Input Sanitization
    └── Request Security Decision
    │
    ▼
AGENT CONTROLLER / ORCHESTRATOR
    │
    ├── Drug / Entity Resolution
    ├── Query Classification
    ├── Retrieval Planning
    │
    ▼
HYBRID RETRIEVAL
(BM25 + Dense / pgvector + Graph / Neo4j)
    │
    ├── Candidate Retrieval
    │
    ▼
RETRIEVED EVIDENCE
    │
    ├── Provenance Validation (NEW)
    ├── Retrieval Poisoning Detection (NEW)
    ├── Content / Metadata Integrity Checks
    ├── Source Validation
    │
    ▼
EVIDENCE ELIGIBILITY GATE
    │
    ▼
TRUST / RERANKING
    │
    ├── Authority
    ├── Freshness
    ├── Entity Alignment
    ├── Integrity
    └── Security
    │
    ▼
EVIDENCE PACK
    │
    ▼
LLM / AGENT REASONING
    │
    ├── Claim Generation
    ├── Tool / Domain Action Requests
    │
    ▼
AUTHORIZATION BOUNDARY (NEW)
    │
    ├── Domain
    ├── Action
    ├── Authorization
    └── Security Policy
    │
    ▼
ALLOWED / BLOCKED / FLAGGED / ESCALATED
    │
    ▼
VERIFICATION
    │
    ├── Claim Support
    ├── Citation Support
    ├── Contradiction Detection
    └── Abstention
    │
    ▼
FINAL ANSWER
    │
    ▼
AUDIT / PROVENANCE / MEMORY
`

## Security Control Points
1. **Prompt Security (Request Edge)**: Intercepts user queries before processing. Ensures malicious inputs do not reach embedding or LLM planning.
2. **Retrieval Security (Post-Retrieval, Pre-Gate)**: Evaluates raw candidates. Prevents poisoned or provenance-tampered documents from advancing to trust evaluation.
3. **Evidence Eligibility**: Combines trust scores with retrieval security outcomes to strictly drop untrusted/unsafe items.
4. **Authorization Boundary (Post-LLM Intent)**: Intercepts structured action requests initiated by the LLM/Agent. Enforces EntityDomain and ActionType policy checks.

## Error Handling & Failure Semantics
- **Prompt Injection Detector Error**: FAIL-CLOSED (Reject query).
- **Retrieval Poisoning Detector Error**: FAIL-SAFE (Drop evidence item).
- **Authorization Boundary Error**: FAIL-CLOSED (Block action).
- **Audit Logging Error**: ESCALATE (Cannot proceed without audit).
