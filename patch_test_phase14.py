import sys
from pathlib import Path

p = Path('tests/security/test_phase14_integration.py')
content = p.read_text(encoding='utf-8')

content = content.replace(
    'metadata={"source": "pubmed", "document_id": "d1"}',
    'metadata={"provenance": {"source": "pubmed", "document_id": "d1"}}'
)
content = content.replace(
    'metadata={"source": "hacked_db"}',
    'metadata={"provenance": {"source": "hacked_db"}}'
)

p.write_text(content, encoding='utf-8')
