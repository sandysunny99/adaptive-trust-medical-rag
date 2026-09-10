import sys
from pathlib import Path

# Fix test_rag_orchestrator
p = Path('tests/test_rag_orchestrator.py')
content = p.read_text(encoding='utf-8')
content = content.replace('assert len(resp.audit_log["steps"]) >= 2', 'assert len(resp.audit_log) >= 2')
p.write_text(content, encoding='utf-8')

# Fix test_phase14_integration
p2 = Path('tests/security/test_phase14_integration.py')
content2 = p2.read_text(encoding='utf-8')
print(content2[:1000])
