import asyncio
import os
import time
from dotenv import load_dotenv
from adaptive_trust_medical_rag.llm_backend.openai_compatible_backend import OpenAICompatibleBackend

load_dotenv('.env')

async def test_provider(name, base_url, api_key, model_name):
    print(f"\n--- Provider: {name} ---")
    if not api_key:
        print("configured: False")
        return
    print("configured: True")
    
    backend = OpenAICompatibleBackend(
        provider_name=name,
        base_url=base_url,
        api_key=api_key,
        model_name=model_name
    )
    
    try:
        t0 = time.time()
        res = await backend.generate("Reply with YES only.")
        t1 = time.time()
        print("endpoint reachable: True")
        print("model available: True")
        print("generate() success: True")
        print(f"generate() latency: {int((t1-t0)*1000)}ms")
    except Exception as e:
        print("generate() success: False", e)
        
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
        t0 = time.time()
        res = await backend.generate_structured("Extract info: return the word HELLO.", response_format=schema)
        t1 = time.time()
        print("generate_structured() success: True")
        print(f"generate_structured() latency: {int((t1-t0)*1000)}ms")
    except Exception as e:
        print("generate_structured() success: False", e)

async def main():
    await test_provider("Groq", "https://api.groq.com/openai/v1", os.environ.get("GROQ_API_KEY"), "openai/gpt-oss-120b")
    await test_provider("NVIDIA", "https://integrate.api.nvidia.com/v1", os.environ.get("NVIDIA_API_KEY"), "nvidia/nemotron-3-super-120b-a12b")
    
    cf_account = os.environ.get('CLOUDFLARE_ACCOUNT_ID')
    if cf_account:
        await test_provider("Cloudflare", f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/v1", os.environ.get("CLOUDFLARE_API_TOKEN"), "@cf/meta/llama-3.3-70b-instruct-fp8-fast")

asyncio.run(main())
