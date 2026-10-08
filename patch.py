content = open('src/adaptive_trust_medical_rag/api/app.py').read()
new_content = content.replace(
'''    primary_provider = os.environ.get("LLM_PROVIDER", "nvidia").lower()

    router = LiveProviderRouter(primary_provider=primary_provider, secondary_provider="groq" if primary_provider == "nvidia" else "nvidia")''',
'''    primary_provider = os.environ.get("LLM_PROVIDER", "nvidia").lower()
    
    provider_priority = []
    if os.environ.get("NVIDIA_API_KEY"): provider_priority.append("nvidia")
    if os.environ.get("GROQ_API_KEY"): provider_priority.append("groq")
    if os.environ.get("HF_TOKEN"): provider_priority.append("huggingface")
    if os.environ.get("CLOUDFLARE_API_TOKEN"): provider_priority.append("cloudflare")
    if os.environ.get("FREELLMAPI_API_KEY"): provider_priority.append("freellm")
    
    if primary_provider in provider_priority:
        provider_priority.remove(primary_provider)
        provider_priority.insert(0, primary_provider)
        
    router = LiveProviderRouter(provider_priority=provider_priority)'''
)
open('src/adaptive_trust_medical_rag/api/app.py', 'w').write(new_content)
