import sys
from pathlib import Path
p = Path('src/adaptive_trust_medical_rag/evaluation/dataset_generator.py')
if p.exists():
    c = p.read_text(encoding='utf-8')
    if '"source_authority"' in c and '"provenance"' not in c:
        c = c.replace(
            '"metadata": {"freshness_score": 0.95}',
            '"metadata": {"freshness_score": 0.95, "provenance": {"source": "pubmed", "document_id": "doc_" + chunk_id}}'
        )
        p.write_text(c, encoding='utf-8')
