import sys
from pathlib import Path
import re

p = Path('src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py')
c = p.read_text(encoding='utf-8')

c = c.replace(
    'self._auth_boundary.authorize(EntityDomain(security_context.principal), ActionType.READ_DATA, request_id, security_context.principal)',
    'self._auth_boundary.authorize(EntityDomain.EVIDENCE, ActionType.READ_DATA, request_id, security_context.principal)'
)

p.write_text(c, encoding='utf-8')
