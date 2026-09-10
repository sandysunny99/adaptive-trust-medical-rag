# Security Extension Architecture

**Phase 12**

## Threat Model Mapping

| Security Control | Implementation | Threat Addressed | Test Coverage | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Sanitization & Stripping** | `security/sanitizer.py` (Existing) | Injection Markers / XSS / PHI | `test_sanitizer.py` | VALIDATED |
| **Prompt Injection Defense** | `PromptInjectionDetector` (New Extension) | Malicious Evidence/Context | `test_prompt_injection_detection` | DEVELOPED |
| **Retrieval Poisoning Defense**| `RetrievalPoisoningDetector` (New Extension) | Document Provenance Spoofing | `test_poisoning_detector_*` | DEVELOPED |
| **Context/Memory Boundary** | `AuthorizationBoundary` (New Extension) | Policy Overrides / Escaping | `test_policy_context_cannot_alter_policy` | DEVELOPED |
| **Tool/Permission Boundary** | `AuthorizationBoundary` (New Extension) | Unauthorized Action Execution | `test_policy_untrusted_data_no_tool_permission` | DEVELOPED |

## Data Flow Architecture

```mermaid
graph TD
    User([USER]) --> Controller(Controller / Agent)
    
    subgraph CONTROL PLANE [TRUSTED]
        Controller
    end
    
    subgraph DATA PLANE [UNTRUSTED]
        Evidence[(Scientific Evidence)]
        Context[Context Engine]
        Memory[(Research Memory)]
    end
    
    Evidence -.-> Controller
    Context -.-> Controller
    Memory -.-> Controller
    
    Controller --> SG{Security Gate}
    
    SG -->|Check 1| PID[Prompt Injection Detection]
    SG -->|Check 2| RPD[Retrieval Poisoning Detection]
    SG -->|Check 3| Auth[Permission / Auth Boundary]
    
    PID --> Verification[Evidence Verification]
    RPD --> Verification
    Auth --> Verification
    
    Verification --> Answer([Final Answer])
```

## Security Posture

- **TRUSTED**: Agent Controller, System Prompts.
- **UNTRUSTED**: User Query, Retrieved Evidence, Session Context, Research Memory.
- **CONTROL PLANE**: Can invoke tools, modify trust/experiment weights.
- **DATA PLANE**: Inert storage. Cannot invoke tools. Cannot execute instructions.
