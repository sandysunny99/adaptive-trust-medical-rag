from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

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
    confidence: float = 1.0
    target: str
    source: str
    evidence_id: Optional[str] = None
    request_id: str
    provenance_reference: Optional[str] = None
    detector: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class SecurityContext(BaseModel):
    request_id: str
    session_id: str
    principal: str = "SYSTEM"
    injection_status: Optional[SecurityDecision] = None
    retrieval_security_states: dict[str, SecurityDecision] = Field(default_factory=dict)
    authorization_states: list[SecurityDecision] = Field(default_factory=list)
    cumulative_decisions: list[SecurityDecision] = Field(default_factory=list)

    def add_decision(self, decision: SecurityDecision):
        self.cumulative_decisions.append(decision)
