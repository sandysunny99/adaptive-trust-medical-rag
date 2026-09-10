# Phase 15 Hardened Specification

## 1. Definition of the Hardened System

The Phase 15 Hardened system is the **actual Phase 14 integrated architecture**. It includes all developed security mechanisms, active gates, and strict boundary enforcement operating directly in the RAG execution path. 

## 2. Configuration State

| Mechanism | Hardened State | Note |
|-----------|----------------|------|
| **Input Sanitization** | `ENABLED` | Standard sanitization. |
| **Prompt Injection Detector** | `ENABLED` | Fail-closed. Blocks malicious injections before retrieval. |
| **Hybrid Retrieval Engine** | `ENABLED` | Standard retrieval. |
| **Retrieval Poisoning Detector** | `ENABLED` | Fail-safe. Excludes candidates with invalid provenance. |
| **Adaptive Trust Scorer** | `ENABLED` | Calculates dynamic trust scores based on entity match, authority, and consistency. |
| **Evidence Eligibility Gate (Gate 1)** | `ENABLED` | Excludes chunks below risk-tier thresholds or exceeding poisoning scores. Triggers abstention if insufficient evidence remains. |
| **LLM Generation** | `ENABLED` | Generates answer based ONLY on eligible, trusted context. |
| **Action Parser** | `ENABLED` | Strict regex extraction. Fail-closed on malformed actions (`ActionParseError` -> Abstention). |
| **Authorization Boundary** | `ENABLED` | Validates Principal, Entity Domain, and Action Type. Unauthorized requests trigger controlled abstention. |
| **Controlled Tool Executor** | `ENABLED` | Executes only authorized actions, recording to audit log. |
| **Answer Safety Gate (Gate 2)** | `ENABLED` | Extracts claims, verifies citations, detects contradictions. Triggers abstention for unsafe outputs. |

## 3. System Identity

The Hardened system evaluated in Phase 15 uses the exact code merged at the conclusion of the Phase 14 engineering freeze. No specialized "evaluation-only" paths or mocks are used for the Hardened configuration.
