import os

file_path = 'src/adaptive_trust_medical_rag/services/live_application.py'
content = open(file_path).read()

# Replace _lazy_init_models(self.app_state) with await asyncio.to_thread(_lazy_init_models, self.app_state)
content = content.replace('_lazy_init_models(self.app_state)', 'await asyncio.to_thread(_lazy_init_models, self.app_state)')

open(file_path, 'w').write(content)
