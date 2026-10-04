import os
import sys
import asyncio
from dotenv import load_dotenv

load_dotenv(".env.local")

async def test_connectivity():
    from adaptive_trust_medical_rag.llm_backend.openai_compatible_backend import OpenAICompatibleBackend
    
    groq = OpenAICompatibleBackend(
        provider_name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ["GROQ_API_KEY"],
        model_name="openai/gpt-oss-120b"
    )
    
    nvidia = OpenAICompatibleBackend(
        provider_name="nvidia",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.environ["NVIDIA_API_KEY"],
        model_name="nvidia/nemotron-3-super-120b-a12b"
    )
    
    # 8. NVIDIA NON-MEDICAL CONNECTIVITY PREFLIGHT
    res_nv = await nvidia.generate("Return exactly NVIDIA_OK")
    print(f"NVIDIA Connectivity: {res_nv.content}")
    
    # 9. GROQ NON-MEDICAL CONNECTIVITY PREFLIGHT
    res_gq = await groq.generate("Return exactly GROQ_OK")
    print(f"GROQ Connectivity: {res_gq.content}")

if __name__ == "__main__":
    asyncio.run(test_connectivity())
