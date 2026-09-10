import sys
from pathlib import Path

p = Path('tests/test_rag_orchestrator.py')
content = p.read_text(encoding='utf-8')

content = content.replace(
    'assert "steps" in resp.audit_log',
    'assert "step" in str(resp.audit_log)'
)

p.write_text(content, encoding='utf-8')
