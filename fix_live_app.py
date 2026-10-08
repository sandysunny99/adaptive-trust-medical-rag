content = open('src/adaptive_trust_medical_rag/services/live_application.py', encoding='utf-8').read()

# Fix asyncio import
if 'import asyncio' not in content:
    content = content.replace('import json', 'import asyncio\nimport json', 1)

# Fix the lazy_init call inside execute()
if 'await asyncio.to_thread(_lazy_init_models' not in content:
    content = content.replace('        start_time = time.time()', '''        start_time = time.time()
        
        try:
            await asyncio.to_thread(_lazy_init_models, self.app_state)
        except Exception as e:
            log.error("Failed to lazy init models: %s", e)''')

open('src/adaptive_trust_medical_rag/services/live_application.py', 'w', encoding='utf-8').write(content)
