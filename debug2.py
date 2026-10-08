content = open('src/adaptive_trust_medical_rag/services/live_application.py').read()
content = content.replace('''
        try:
            await asyncio.to_thread(_lazy_init_models, self.app_state)
        except Exception as e:
''', '''
        try:
            print("DEBUG: BEFORE to_thread")
            await asyncio.to_thread(_lazy_init_models, self.app_state)
            print("DEBUG: AFTER to_thread")
        except Exception as e:
            print(f"DEBUG: to_thread EXCEPTION {e}")
''')
open('src/adaptive_trust_medical_rag/services/live_application.py', 'w').write(content)
