"""Security Extensions - Phase 12.

Isolated security layer wrapping the agent. Prevents retrieved evidence,
context, and memory (untrusted data) from acting as control channels.
"""
from .boundary_enforcer import ActionType, AuthorizationBoundary, EntityDomain
from .injection_detector import PromptInjectionDetector
from .poisoning_detector import RetrievalPoisoningDetector

__all__ = [
    "PromptInjectionDetector", "InjectionDecision",
    "RetrievalPoisoningDetector", "",
    "AuthorizationBoundary", "EntityDomain", "ActionType"
]
