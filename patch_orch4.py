import sys
from pathlib import Path

p = Path('src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py')
content = p.read_text(encoding='utf-8')

import re
content = re.sub(
    r'\) -> RAGResponse:\n        \"\"\"Return a structured abstention response\.\"\"\"        security_context: SecurityContext \| None = None,\n    \) -> RAGResponse:',
    '    security_context: SecurityContext | None = None,\n    ) -> RAGResponse:\n        """Return a structured abstention response."""',
    content,
    flags=re.DOTALL
)

p.write_text(content, encoding='utf-8')
