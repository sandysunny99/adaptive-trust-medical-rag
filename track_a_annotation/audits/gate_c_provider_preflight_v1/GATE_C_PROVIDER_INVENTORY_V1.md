# Provider Inventory

1. **Groq**
   - Adapter: src/adaptive_trust_medical_rag/llm_backend/groq_backend.py
   - Model: openai/gpt-oss-120b
   - Endpoint: https://api.groq.com/openai/v1/chat/completions
   - Credential: GROQ_API_KEY
   - Dependency: httpx
   - Status: Primary candidate

2. **Gemini** (FROZEN FOR PHASE 15)
   - Adapter: src/adaptive_trust_medical_rag/llm_backend/google_gemini_backend.py
   - Model: gemini-3.1-pro-preview
   - Credential: GEMINI_API_KEY

3. **Cloudflare Workers AI**
   - Adapter: src/adaptive_trust_medical_rag/llm_backend/cloudflare_backend.py
   - Model: @cf/meta/llama-3.3-70b-instruct-fp8-fast
   - Credential: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID

4. **HuggingFace Inference**
   - Adapter: src/adaptive_trust_medical_rag/llm_backend/huggingface_backend.py
   - Model: meta-llama/Llama-3.3-70B-Instruct
   - Credential: HF_TOKEN