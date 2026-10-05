from enum import Enum

from adaptive_trust_medical_rag.security.security_context import SecurityDecision, SecurityState


class EntityDomain(Enum):
    SYSTEM = "SYSTEM"            # Trusted Control Plane
    USER = "USER"                # Untrusted External
    EVIDENCE = "EVIDENCE"        # Untrusted Data Plane
    CONTEXT = "CONTEXT"          # Untrusted Data Plane
    MEMORY = "MEMORY"            # Untrusted Data Plane

class ActionType(Enum):
    READ_DATA = "READ_DATA"
    WRITE_MEMORY = "WRITE_MEMORY"
    WRITE_CONTEXT = "WRITE_CONTEXT"
    MODIFY_TRUST_CONFIG = "MODIFY_TRUST_CONFIG"
    MODIFY_EXPERIMENT_CONFIG = "MODIFY_EXPERIMENT_CONFIG"
    INVOKE_TOOL = "INVOKE_TOOL"

class AuthorizationBoundary:
    """Enforces boundaries between Trusted Control Plane and Untrusted Data Plane."""

    def __init__(self):
        # Policy defines what a principal can do on a target domain.
        # Format: { principal_name: { target_domain: { allowed_actions } } }
        self._policy = {
            "SYSTEM": {
                EntityDomain.SYSTEM: {ActionType.READ_DATA, ActionType.WRITE_MEMORY, ActionType.WRITE_CONTEXT, ActionType.MODIFY_TRUST_CONFIG, ActionType.MODIFY_EXPERIMENT_CONFIG, ActionType.INVOKE_TOOL},
                EntityDomain.USER: {ActionType.READ_DATA},
                EntityDomain.EVIDENCE: {ActionType.READ_DATA},
                EntityDomain.CONTEXT: {ActionType.READ_DATA, ActionType.WRITE_CONTEXT},
                EntityDomain.MEMORY: {ActionType.READ_DATA, ActionType.WRITE_MEMORY},
            },
            "USER": {
                EntityDomain.EVIDENCE: {ActionType.READ_DATA},
                EntityDomain.CONTEXT: {ActionType.READ_DATA},
                EntityDomain.MEMORY: {ActionType.READ_DATA},
            },
            # EVIDENCE, CONTEXT, MEMORY cannot act as principals to perform actions
        }

    def authorize(self, domain: EntityDomain, action: ActionType, request_id: str, principal: str) -> SecurityDecision:
        """Check if a principal is authorized to perform an action on a target domain."""
        allowed_actions = self._policy.get(principal, {}).get(domain, set())

        if action not in allowed_actions:
            return SecurityDecision(
                decision=SecurityState.UNAUTHORIZED_ACTION_REJECTED,
                reason_code="AUTHORIZATION_REJECTED",
                attack_family="BOUNDARY_VIOLATION",
                attack_subtype=f"{principal}_TO_{domain.value}_{action.value}",
                confidence=1.0,
                target="action_executor",
                source=principal,
                request_id=request_id,
                detector="AuthorizationBoundary"
            )

        return SecurityDecision(
            decision=SecurityState.ALLOW,
            reason_code="AUTHORIZATION_GRANTED",
            attack_family="BOUNDARY_VIOLATION",
            confidence=1.0,
            target="action_executor",
            source=principal,
            request_id=request_id,
            detector="AuthorizationBoundary"
        )
