import asyncio
import os
import json
from dotenv import load_dotenv
from adaptive_trust_medical_rag.llm_backend.openai_compatible_backend import OpenAICompatibleBackend

load_dotenv('.env')

async def test_hf1():
    token = os.environ.get('HF_TOKEN')
    print('Testing HF router...')
    backend = OpenAICompatibleBackend(
        provider_name="HuggingFace",
        base_url="https://api-inference.huggingface.co/models/meta-llama/Llama-3.3-70B-Instruct/v1",
        api_key=token,
        model_name="meta-llama/Llama-3.3-70B-Instruct"
    )
    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "test",
            "schema": {
                "type": "object",
                "properties": {"word": {"type": "string"}},
                "required": ["word"]
            }
        }
    }
    try:
        resp = await backend.generate_structured("Return the word HELLO.", response_format=schema)
        print('HF SUCCESS:', resp.structured_output)
    except Exception as e:
        print('HF FAILED:', e)

asyncio.run(test_hf1())
