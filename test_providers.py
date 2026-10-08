import asyncio
import os
import json
from dotenv import load_dotenv
from adaptive_trust_medical_rag.llm_backend.openai_compatible_backend import OpenAICompatibleBackend

load_dotenv('.env')

async def test_hf():
    token = os.environ.get('HF_TOKEN')
    print('Testing HF...')
    backend = OpenAICompatibleBackend(
        provider_name="HuggingFace",
        base_url="https://api-inference.huggingface.co/v1",
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

async def test_cf():
    token = os.environ.get('CLOUDFLARE_API_TOKEN')
    account = os.environ.get('CLOUDFLARE_ACCOUNT_ID')
    print('Testing CF...')
    backend = OpenAICompatibleBackend(
        provider_name="Cloudflare",
        base_url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1",
        api_key=token,
        model_name="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
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
        print('CF SUCCESS:', resp.structured_output)
    except Exception as e:
        print('CF FAILED:', e)

async def main():
    await test_hf()
    await test_cf()

asyncio.run(main())
