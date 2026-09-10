# Phase 14 Security Contracts

## 1. Security Decision Schema
A canonical decision model for all security components.

`python
from enum import Enum
from pydantic import BaseModel
from typing import Optional, Any

class SecurityState(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    FLAG = "FLAG"
    ESCALATE = "ESCALATE"
    UNAUTHORIZED_ACTION_REJECTED = "UNAUTHORIZED_ACTION_REJECTED"

class SecurityDecision(BaseModel):
    decision: SecurityState
    reason_code: str
    attack_family: str
    attack_subtype: Optional[str] = None
    confidence: float
    target: str                  # e.g., "orchestrator", "retriever", "action"
    source: str                  # e.g., "user_query", "document_D17", "llm_agent"
    evidence_id: Optional[str] = None
    request_id: str
    provenance_reference: Optional[str] = None
    detector: str                # e.g., "PromptInjectionDetector"
    timestamp: str               # ISO 8601
`

## 2. Security Context
Propagates the security state throughout the request lifecycle.

`python
class SecurityContext(BaseModel):
    request_id: str
    session_id: str
    principal: str
    injection_status: SecurityDecision
    retrieval_security_states: dict[str, SecurityDecision] # Keyed by chunk_id
    authorization_states: list[SecurityDecision]
    cumulative_decisions: list[SecurityDecision]
`

## 3. Detector Contracts

### Prompt Injection Detector
- **Input**: User Query (str)
- **Output**: SecurityDecision
- **Behavior**: Inspects query prior to embedding. If BLOCK, halts execution.

### Retrieval Poisoning Detector
- **Input**: Retrieved Candidates (list[EvidenceChunk])
- **Output**: dict[str, SecurityDecision] (Keyed by chunk_id)
- **Behavior**: Inspects provenance, hash integrity, and content. Does not silently drop, but assigns a security state per chunk.

## 4. Evidence Eligibility Contract
- **Input**: etrieved_chunks, 	rust_scores, etrieval_security_states
- **Rule**:
  chunk.eligible = (trust_score >= threshold) AND (retrieval_security_states[chunk.id].decision == ALLOW)
- **Output**: EligibilityResult

## 5. Authorization Contract
- **Input**: EntityDomain, ActionType, SecurityContext
- **Behavior**: Validates whether the active principal/context has permission to execute the action on the domain.
- **Output**: SecurityDecision (ALLOW or UNAUTHORIZED_ACTION_REJECTED).

## 6. Audit Contract
- **Behavior**: Every SecurityDecision generated must be appended to the central udit_log with the exact structure from the Security Decision Schema.
