content = open('src/adaptive_trust_medical_rag/services/live_application.py').read()
content = content.replace('import json\nimport dataclasses', 'import json\n            import dataclasses')
open('src/adaptive_trust_medical_rag/services/live_application.py', 'w').write(content)
