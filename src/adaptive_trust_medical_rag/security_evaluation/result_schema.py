from dataclasses import dataclass
from typing import Any

from .security_case import AttackFamily, EvaluationCondition, ExpectedOutcome


@dataclass
class SecurityResultRecord:
    evaluation_id: str
    case_id: str
    condition: EvaluationCondition
    case_input_hash: str
    attack_family: AttackFamily
    attack_subtype: str
    expected_outcome: ExpectedOutcome
    observed_outcome: str
    detected: bool
    blocked: bool
    false_positive: bool
    unauthorized_action: bool
    provenance_preserved: bool
    requires_provenance_preservation: bool
    requires_authorization_check: bool
    security_decision: str
    reason_code: str
    harness_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "case_id": self.case_id,
            "condition": self.condition.value,
            "case_input_hash": self.case_input_hash,
            "attack_family": self.attack_family.value,
            "attack_subtype": self.attack_subtype,
            "expected_outcome": self.expected_outcome.value,
            "observed_outcome": self.observed_outcome,
            "detected": self.detected,
            "blocked": self.blocked,
            "false_positive": self.false_positive,
            "unauthorized_action": self.unauthorized_action,
            "provenance_preserved": self.provenance_preserved,
            "requires_provenance_preservation": self.requires_provenance_preservation,
            "requires_authorization_check": self.requires_authorization_check,
            "security_decision": self.security_decision,
            "reason_code": self.reason_code,
            "harness_version": self.harness_version,
        }
