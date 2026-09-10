from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import re
from adaptive_trust_medical_rag.security_extensions.boundary_enforcer import EntityDomain, ActionType


class ActionParseError(Exception):
    """Raised when LLM output cannot be parsed into a valid action request."""
    pass


@dataclass(frozen=True)
class AgentActionRequest:
    """Typed representation of a structured action request from LLM output."""
    principal: str
    entity_domain: EntityDomain
    action_type: ActionType
    target: str
    request_id: str
    arguments: dict[str, Any] | None = None


_ACTION_PATTERN = re.compile(r"\[ACTION:\s*([A-Z_]+)\s+ON\s+([A-Z_]+)\]")


def parse_action_request(
    llm_output: str,
    principal: str,
    request_id: str,
) -> AgentActionRequest | None:
    """
    Parse structured action requests from LLM output.
    
    Returns None if no action marker is found (output is a normal claim).
    Raises ActionParseError if an action marker is found but malformed.
    
    FAIL-CLOSED: Any parse error results in ActionParseError, never
    a fallback to a default privileged action.
    """
    match = _ACTION_PATTERN.search(llm_output)
    if not match:
        return None  # No action in output — it's a normal claim response
    
    action_type_str = match.group(1)
    domain_str = match.group(2)
    
    # Validate action type — fail closed on unknown
    try:
        action_type = ActionType(action_type_str)
    except ValueError:
        raise ActionParseError(
            f"Unknown action type: '{action_type_str}'. "
            f"Valid types: {[a.value for a in ActionType]}"
        )
    
    # Validate domain — fail closed on unknown
    try:
        domain = EntityDomain(domain_str)
    except ValueError:
        raise ActionParseError(
            f"Unknown entity domain: '{domain_str}'. "
            f"Valid domains: {[d.value for d in EntityDomain]}"
        )
    
    return AgentActionRequest(
        principal=principal,
        entity_domain=domain,
        action_type=action_type,
        target=f"{domain.value}/{action_type.value}",
        request_id=request_id,
    )
