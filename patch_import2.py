import os

file_path = 'src/adaptive_trust_medical_rag/services/live_application.py'
content = open(file_path).read()

content = content.replace('''            from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import (
                Candidate,
                HybridRetrievalEngine,
            )''', '')

import_str2 = '''from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate, HybridRetrievalEngine\n'''
if "HybridRetrievalEngine" not in content[:1000]:
    content = content.replace('import asyncio', 'import asyncio\n' + import_str2)

open(file_path, 'w').write(content)
