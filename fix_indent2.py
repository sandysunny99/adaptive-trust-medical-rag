content = open('src/adaptive_trust_medical_rag/services/live_application.py').read()
content = content.replace('            import dataclasses\n', '')
content = content.replace('import json', 'import dataclasses\nimport json', 1)
open('src/adaptive_trust_medical_rag/services/live_application.py', 'w').write(content)
