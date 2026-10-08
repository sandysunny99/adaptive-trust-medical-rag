content = open('src/adaptive_trust_medical_rag/verification/claim_verifier_v2.py').read()
content = content.replace('import re', 'import os\nimport re')
open('src/adaptive_trust_medical_rag/verification/claim_verifier_v2.py', 'w').write(content)
