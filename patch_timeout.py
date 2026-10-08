content = open('src/adaptive_trust_medical_rag/services/live_application.py').read()
content = content.replace('''                if confirmation_event and "confirmed_medications" not in analysis_state:
                    await confirmation_event.wait()''', '''                if confirmation_event and "confirmed_medications" not in analysis_state:
                    try:
                        await asyncio.wait_for(confirmation_event.wait(), timeout=10.0)
                    except asyncio.TimeoutError:
                        yield _sse("error", {"code": "TIMEOUT", "message": "Confirmation timeout"})
                        return''')
open('src/adaptive_trust_medical_rag/services/live_application.py', 'w').write(content)
