import asyncio
import os
from dotenv import load_dotenv
from adaptive_trust_medical_rag.api.app import router

load_dotenv('.env')

async def test_live_failover():
    print("--- Test 1: Real success ---")
    try:
        res = await router.generate("Return the word HELLO.")
        print("Success from:", res.provider)
    except Exception as e:
        print("Failed:", e)

    print("\n--- Test 2: Simulate Primary 429 -> Fallback ---")
    # Temporarily replace primary generate with a mock 429
    primary_name = router.provider_priority[0]
    primary_backend = router.providers[primary_name]
    original_generate = primary_backend.generate
    
    from adaptive_trust_medical_rag.common.model_result import ModelExecutionError
    from adaptive_trust_medical_rag.llm_routing.types import FailureClass
    
    async def mock_429(*args, **kwargs):
        err = ModelExecutionError("Mocked 429", status_code="429")
        err.failure_class = FailureClass.RATE_LIMIT
        raise err
        
    primary_backend.generate = mock_429
    
    try:
        res = await router.generate("Return the word HELLO.")
        print("Success from:", res.provider)
    except Exception as e:
        print("Failed:", e)
        
    print("\n--- Test 3: Simulate Primary 429, Secondary 503 -> Tertiary Fallback ---")
    secondary_name = router.provider_priority[1]
    secondary_backend = router.providers[secondary_name]
    original_generate_2 = secondary_backend.generate
    
    async def mock_503(*args, **kwargs):
        err = ModelExecutionError("Mocked 503", status_code="503")
        err.failure_class = FailureClass.TRANSIENT_PROVIDER
        raise err
        
    secondary_backend.generate = mock_503
    
    try:
        res = await router.generate("Return the word HELLO.")
        print("Success from:", res.provider)
    except Exception as e:
        print("Failed:", e)

    # Restore
    primary_backend.generate = original_generate
    secondary_backend.generate = original_generate_2

asyncio.run(test_live_failover())
