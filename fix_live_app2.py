content = open('src/adaptive_trust_medical_rag/services/live_application.py', encoding='utf-8').read()

if 'await asyncio.to_thread(_lazy_init_models' not in content:
    content = content.replace('        """Execute the live pipeline and yield SSE event dicts."""', '''        """Execute the live pipeline and yield SSE event dicts."""
        try:
            await asyncio.to_thread(_lazy_init_models, self.app_state)
        except Exception as e:
            log.error("Failed to lazy init models: %s", e)''')

open('src/adaptive_trust_medical_rag/services/live_application.py', 'w', encoding='utf-8').write(content)
