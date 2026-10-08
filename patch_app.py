import os
import re

app_file = 'src/adaptive_trust_medical_rag/api/app.py'
content = open(app_file).read()

# I want to remove the initialization of claim_verifier and retrieval_engine from create_app,
# and instead leave them as None in create_app.
# I will just write a patch for app.py to replace the block.
