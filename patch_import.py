import os

file_path = 'src/adaptive_trust_medical_rag/services/live_application.py'
content = open(file_path).read()

# Replace the inner import with a global import if not present
content = content.replace('from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2\n', '')

# add global import
import_str = "from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2\n"
if "ClaimVerifierV2" not in content[:1000]:
    content = content.replace('from adaptive_trust_medical_rag.verification.claim_verifier_v2 import (', import_str + 'from adaptive_trust_medical_rag.verification.claim_verifier_v2 import (')

open(file_path, 'w').write(content)
