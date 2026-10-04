# Taxonomic Threat & Control Crosswalk

This document provides a taxonomic crosswalk between the Adaptive Trust-Aware Medical RAG's custom security controls and established industry threat and risk frameworks. 

> [!NOTE]
> This is a **Taxonomic Threat/Control Crosswalk**, NOT a certification of compliance. 
> "NIST AI RMF Alignment" indicates conceptual alignment with NIST's voluntary playbook guidance, not a mandatory implementation checklist.
> "MITRE ATLAS" indicates threat mapping, not compliance.

## Threat → Control Crosswalk

| Threat / Attack Surface | MITRE ATLAS Technique | Project Control | NIST AI RMF Alignment | Project Test / Evidence |
|---|---|---|---|---|
| **Direct prompt injection** | **AML.T0051** (Direct) | `PromptInjectionDetector` + `InputSanitizer` | MANAGE security-risk controls; MEASURE 2.6/2.7 | Security evaluation harness (BASELINE vs HARDENED) |
| **Indirect prompt injection** (via retrieved content) | **AML.T0051** (Indirect) | Retrieval sanitization + `EvidenceEligibilityGate` | MAP 4.1/4.2; MEASURE 2.7 | Poisoned context retrieval test cases |
| **Crafted adversarial evidence** | **AML.T0043** | `RetrievalPoisoningDetector` | MAP 2.3 / MAP 4.1 / MEASURE 2.7 | Anomaly score tracking, adversarial chunk injection tests |
| **Compromised upstream evidence/data** | **AML.T0010.002** | Source validation + provenance + integrity checks | MAP 4.1/4.2 | Missing provenance rejection tests |
| **Unauthorized agent tool use** | **AML.T0053** | `AuthorizationBoundary` + `ToolExecutor` | MAP 3.5; MEASURE 2.7 | Domain boundary violation test cases |
| **Jailbreak attempting to bypass model safeguards** | **AML.T0054** | Prompt/security gates | MANAGE / MEASURE security controls | Security evaluation suite |
| **Model/inference API abuse** | **AML.T0040** | Provider/API controls, RateLimitInfo | MAP 4.1 / 4.2 | Router failure & failover tests |

## Conceptual Mapping Definitions

*   **MITRE ATLAS**: Used to define the *adversarial technique* and *attack surface* that the system is defending against.
*   **NIST AI RMF**: Used to map the *nature of the risk management* being performed (e.g., MAP for establishing context and capabilities, MEASURE for quantitative/qualitative evaluation, MANAGE for active risk mitigation).
