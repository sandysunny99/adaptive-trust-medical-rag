import sys
from pathlib import Path

p = Path('src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py')
content = p.read_text(encoding='utf-8')

import re
content = re.sub(
    r'    audit_log: dict\n    generated_at',
    '    audit_log: dict\n    security_events: list[SecurityDecision] = field(default_factory=list)\n    generated_at',
    content
)

p.write_text(content, encoding='utf-8')
