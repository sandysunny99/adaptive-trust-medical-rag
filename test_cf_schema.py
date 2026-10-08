import asyncio
import os
import json
from dotenv import load_dotenv
from adaptive_trust_medical_rag.llm_backend.openai_compatible_backend import OpenAICompatibleBackend

load_dotenv('.env')

async def test_cf():
    token = os.environ.get('CLOUDFLARE_API_TOKEN')
    account = os.environ.get('CLOUDFLARE_ACCOUNT_ID')
    backend = OpenAICompatibleBackend(
        provider_name="Cloudflare",
        base_url=f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1",
        api_key=token,
        model_name="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
    )
    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "complex",
            "schema": {
                "type": "object",
                "properties": {
                    "drug_name": {"type": "string"},
                    "dose_mg": {"type": "integer"}
                },
                "required": ["drug_name", "dose_mg"]
            }
        }
    }
    try:
        resp = await backend.generate_structured("Extract info: I took 500 mg of Tylenol.", response_format=schema)
        print('CF SUCCESS:', resp.structured_output)
    except Exception as e:
        print('CF FAILED:', e)

asyncio.run(test_cf())
