content = open('src/adaptive_trust_medical_rag/services/live_application.py').read()
content = content.replace('e.__dict__', 'dataclasses.asdict(e)')
if 'import dataclasses' not in content:
    content = content.replace('import json', 'import json\nimport dataclasses')
open('src/adaptive_trust_medical_rag/services/live_application.py', 'w').write(content)
