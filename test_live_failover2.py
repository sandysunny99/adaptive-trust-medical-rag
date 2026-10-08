import asyncio
import os
from dotenv import load_dotenv
from adaptive_trust_medical_rag.llm_backend.live_provider_router import LiveProviderRouter
from adaptive_trust_medical_rag.llm_backend.openai_compatible_backend import OpenAICompatibleBackend
from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
from adaptive_trust_medical_rag.llm_routing.types import FailureClass

load_dotenv('.env')

async def test_live_failover():
    provider_priority = ["nvidia", "cloudflare"]
    router = LiveProviderRouter(provider_priority=provider_priority)

    nvidia_backend = OpenAICompatibleBackend(
        provider_name="nvidia",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.environ.get("NVIDIA_API_KEY"),
        model_name="nvidia/nemotron-3-super-120b-a12b"
    )
    router.register_provider("nvidia", nvidia_backend)

    cloudflare_backend = OpenAICompatibleBackend(
        provider_name="cloudflare",
        base_url=f"https://api.cloudflare.com/client/v4/accounts/{os.environ.get('CLOUDFLARE_ACCOUNT_ID')}/ai/v1",
        api_key=os.environ.get("CLOUDFLARE_API_TOKEN"),
        model_name="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
    )
    router.register_provider("cloudflare", cloudflare_backend)

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

    print("--- Test 1: Real success ---")
    try:
        res = await router.generate_structured("Return the word HELLO.", schema)
        print("Success from:", res.provider)
    except Exception as e:
        print("Failed:", type(e).__name__, e)

    print("\n--- Test 2: Simulate Primary 429 -> Fallback ---")
    original_generate = nvidia_backend.generate_structured
    
    async def mock_429(*args, **kwargs):
        err = ModelExecutionError("Mocked 429", status_code="429")
        err.failure_class = FailureClass.RATE_LIMIT
        raise err
        
    nvidia_backend.generate_structured = mock_429
    
    try:
        res = await router.generate_structured("Return the word HELLO.", schema)
        print("Success from:", res.provider)
    except Exception as e:
        print("Failed:", type(e).__name__, e)
        
    print("\n--- Test 3: Simulate Primary 429, Secondary 503 -> Final Error ---")
    original_generate_2 = cloudflare_backend.generate_structured
    
    async def mock_503(*args, **kwargs):
        err = ModelExecutionError("Mocked 503", status_code="503")
        err.failure_class = FailureClass.TRANSIENT_PROVIDER
        raise err
        
    cloudflare_backend.generate_structured = mock_503
    
    try:
        res = await router.generate_structured("Return the word HELLO.", schema)
        print("Success from:", res.provider)
    except Exception as e:
        print("Failed:", type(e).__name__, e)

asyncio.run(test_live_failover())
