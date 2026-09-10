import sys
from pathlib import Path

p = Path('src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py')
content = p.read_text(encoding='utf-8')

content = content.replace(
    '_log("session_start", {"session_id": session_id, "query": request.query})',
    '_log("session_start", {"session_id": session_id})'
)

p.write_text(content, encoding='utf-8')
