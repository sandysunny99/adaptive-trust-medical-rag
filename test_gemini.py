import asyncio
import os
from dotenv import load_dotenv
from adaptive_trust_medical_rag.llm_backend.openai_compatible_backend import OpenAICompatibleBackend

load_dotenv('.env')
api_key = os.environ.get('GEMINI_API_KEY')
if not api_key:
    print('No GEMINI_API_KEY')
    exit(1)

async def test_gemini():
    backend = OpenAICompatibleBackend(
        provider_name="Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        api_key=api_key,
        model_name="gemini-1.5-flash"
    )
    # Test unstructured
    try:
        resp = await backend.generate("Return the word HELLO.")
        print('generate() SUCCESS:', resp.content)
    except Exception as e:
        print('generate() FAILED:', e)

    # Test structured
    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "test_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "word": {"type": "string"}
                },
                "required": ["word"]
            }
        }
    }
    try:
        resp2 = await backend.generate_structured("Return the word HELLO.", response_format=schema)
        print('generate_structured() SUCCESS:', resp2.structured_output)
    except Exception as e:
        print('generate_structured() FAILED:', e)

asyncio.run(test_gemini())
