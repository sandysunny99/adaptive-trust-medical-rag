import os

file_path = 'src/adaptive_trust_medical_rag/services/live_application.py'
content = open(file_path).read()

search_str = '''                # Wait for the frontend to confirm
                confirmation_event = analysis_state.get("confirmation_event")
                if confirmation_event:
                    await confirmation_event.wait()'''

replace_str = '''                # Wait for the frontend to confirm
                confirmation_event = analysis_state.get("confirmation_event")
                if confirmation_event and "confirmed_medications" not in analysis_state:
                    await confirmation_event.wait()'''

content = content.replace(search_str, replace_str)
open(file_path, 'w').write(content)
