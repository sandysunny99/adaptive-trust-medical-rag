content = open('src/adaptive_trust_medical_rag/services/live_application.py').read()
content = content.replace('e.model_dump()', 'e.__dict__')
open('src/adaptive_trust_medical_rag/services/live_application.py', 'w').write(content)
