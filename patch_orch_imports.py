import sys
from pathlib import Path

p = Path('src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py')
content = p.read_text(encoding='utf-8')

# We need to insert imports at the top
if 'SecurityDecision' not in content:
    content = content.replace(
        'from dataclasses import dataclass, field',
        'from dataclasses import dataclass, field\nfrom adaptive_trust_medical_rag.security.security_context import SecurityDecision, SecurityState, SecurityContext\nfrom adaptive_trust_medical_rag.security_extensions.injection_detector import PromptInjectionDetector\nfrom adaptive_trust_medical_rag.security_extensions.poisoning_detector import RetrievalPoisoningDetector\nfrom adaptive_trust_medical_rag.security_extensions.boundary_enforcer import AuthorizationBoundary, EntityDomain, ActionType'
    )

if 'security_events: list[SecurityDecision]' not in content:
    content = content.replace(
        '    audit_log: list[dict[str, Any]]',
        '    audit_log: list[dict[str, Any]]\n    security_events: list[SecurityDecision] = field(default_factory=list)'
    )

p.write_text(content, encoding='utf-8')
