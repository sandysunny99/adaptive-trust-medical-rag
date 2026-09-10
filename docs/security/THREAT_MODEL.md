# Threat Model: Adaptive Trust-Aware Pharmacology Evidence Agent

## Assets
- **Scientific Evidence** (Documents, citations, drug labels)
- **Agent Context** (Temporary task state)
- **Research Memory** (Historical logs, decisions)
- **Trust Configuration** (AdaptiveTrustScorer weights)
- **Experiment Configuration** (Experiment tracker state)

## Trust Boundaries
- **TRUSTED**: System Control Plane, System Prompt, Controller Logic
- **UNTRUSTED**: User Input, Retrieved Evidence, Session Context, Research Memory

## Threat Actors
- External Users (attempting prompt injection)
- Malicious/Compromised Data Sources (retrieval poisoning)
- Insider Threats (attempting to modify canonical experiment state)

## Attack Surfaces

### 1. Prompt Injection
- **Threat**: Instructions embedded in user queries or retrieved documents that attempt to hijack the control plane.
- **Mitigation**: `PromptInjectionDetector` leveraging deterministic sanitization. Retrieved content is treated strictly as inert data.

### 2. Retrieval Poisoning
- **Threat**: Maliciously crafted documents ingested into the vector/graph database to manipulate trust scores or drug interaction summaries.
- **Mitigation**: `RetrievalPoisoningDetector` inspecting document provenance. Source authority rules preventing untrusted domains from being scored highly.

### 3. Context/Memory Manipulation
- **Threat**: Context or Memory attempting to rewrite trust weights, experiment rules, or system policies.
- **Mitigation**: Strict `AuthorizationBoundary` preventing `CONTEXT` and `MEMORY` from invoking tools or executing control plane actions (`MODIFY_TRUST_CONFIG`).

### 4. Unauthorized Tool Invocation
- **Threat**: Untrusted evidence or user inputs directly invoking sensitive tools.
- **Mitigation**: `AuthorizationBoundary` mapping `EVIDENCE`, `USER`, and `CONTEXT` to an inert authorization matrix (`READ_DATA` only).

## Residual Risks
- Advanced adversarial prompt injections bypassing regex heuristics.
- State-sponsored poisoning of trusted medical literature sources (e.g., PubMed).
