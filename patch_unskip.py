import sys
from pathlib import Path

p = Path('tests/security/test_phase14_integration.py')
c = p.read_text(encoding='utf-8')
c = c.replace('@pytest.mark.skip\ndef test_retrieval_poisoning_excluded', 'def test_retrieval_poisoning_excluded')
p.write_text(c, encoding='utf-8')
