content = open('src/adaptive_trust_medical_rag/api/app.py').read()
new_content = content.replace(
'''    if nvidia_api_key:
        nvidia_backend = OpenAICompatibleBackend(
            provider_name="nvidia",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_api_key,
            model_name="nvidia/nemotron-3-super-120b-a12b"
        )
        router.register_provider("nvidia", nvidia_backend)''',
'''    if nvidia_api_key:
        nvidia_backend = OpenAICompatibleBackend(
            provider_name="nvidia",
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_api_key,
            model_name="nvidia/nemotron-3-super-120b-a12b"
        )
        router.register_provider("nvidia", nvidia_backend)
        
    if os.environ.get("HF_TOKEN"):
        # Note: HF backend does not currently implement ProviderAdapter structured generation natively
        # we will register it for future completeness, but the router should handle it cleanly
        try:
            from adaptive_trust_medical_rag.llm_backend.huggingface_backend import HuggingFaceBackend
            router.register_provider("huggingface", HuggingFaceBackend(os.environ["HF_TOKEN"]))
        except ImportError:
            pass
            
    if os.environ.get("CLOUDFLARE_API_TOKEN") and os.environ.get("CLOUDFLARE_ACCOUNT_ID"):
        try:
            from adaptive_trust_medical_rag.llm_backend.cloudflare_backend import CloudflareBackend
            router.register_provider("cloudflare", CloudflareBackend(
                os.environ["CLOUDFLARE_API_TOKEN"], 
                os.environ["CLOUDFLARE_ACCOUNT_ID"]
            ))
        except ImportError:
            pass'''
)
open('src/adaptive_trust_medical_rag/api/app.py', 'w').write(new_content)
