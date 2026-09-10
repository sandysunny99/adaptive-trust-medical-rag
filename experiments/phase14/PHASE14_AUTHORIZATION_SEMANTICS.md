# Phase 14 Authorization Semantics

## 1. Core Principles

The authorization architecture strictly decouples three distinct concepts:
- **PRINCIPAL:** The authenticated identity making the request (e.g., `SYSTEM`, `USER`).
- **ENTITY DOMAIN:** The boundary of the resource being acted upon (e.g., `EVIDENCE`, `SYSTEM`, `MEMORY`).
- **ACTION TYPE:** The specific operation being attempted (e.g., `READ_DATA`, `INVOKE_TOOL`).

## 2. LLM Generation vs. Action Execution

LLM generation itself is **not** a privileged action. The system distinguishes between:
1. **Synthesizing Evidence (Normal Flow):** The LLM receives retrieved evidence in its context and generates a claim-based answer. The principal (`USER`) is authorized to `READ_DATA` on `EVIDENCE` implicitly by the pipeline.
2. **Structured Actions (Tool Flow):** The LLM outputs a specific tool request marker (e.g., `[ACTION: INVOKE_TOOL ON SYSTEM]`). This is intercepted *after* generation.

## 3. Fail-Closed Parsing

All structured action parsing is **fail-closed**:
- A malformed action marker (e.g., unknown action type, unknown domain) results in an `ActionParseError`.
- The system **never** falls back to a default action type (e.g., promoting a bad parse to `INVOKE_TOOL` on `SYSTEM`).
- A parsing error results in a controlled system abstention, ensuring no unintended operations execute.

## 4. Controlled Execution

Authorized actions are routed through a dedicated `ToolExecutor`.
- The executor validates the authorization decision.
- It logs the `request_id`, `principal`, `action_type`, and `entity_domain`.
- Currently, execution is simulated (no-op) to establish the architectural boundary, but the integration path is fully verified.

## 5. Policy Matrix

| Principal | Target Domain | Allowed Actions |
|-----------|---------------|-----------------|
| `SYSTEM` | `SYSTEM` | `READ_DATA`, `WRITE_MEMORY`, `WRITE_CONTEXT`, `MODIFY_TRUST_CONFIG`, `MODIFY_EXPERIMENT_CONFIG`, `INVOKE_TOOL` |
| `SYSTEM` | `USER` | `READ_DATA` |
| `SYSTEM` | `EVIDENCE` | `READ_DATA` |
| `SYSTEM` | `CONTEXT` | `READ_DATA`, `WRITE_CONTEXT` |
| `SYSTEM` | `MEMORY` | `READ_DATA`, `WRITE_MEMORY` |
| `USER` | `EVIDENCE` | `READ_DATA` |
| `USER` | `CONTEXT` | `READ_DATA` |
| `USER` | `MEMORY` | `READ_DATA` |

*Untrusted data planes (`EVIDENCE`, `CONTEXT`, `MEMORY`) cannot act as principals.*
