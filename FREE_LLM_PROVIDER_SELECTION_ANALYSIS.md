# Free LLM Provider Selection Analysis

## Overview
The provided repository `mnfst/awesome-free-llm-apis` is a curated list of free-tier and permanent-free LLM API providers, many of which use OpenAI-compatible SDK endpoints. It is **not** a single combined API service, nor does it pool quotas. 

## Evaluation Criteria for Medical RAG
To integrate a provider into the Live Multi-Provider Router, the provider must support:
1. **OpenAI-Compatible API**: For seamless integration with our `OpenAICompatibleBackend`.
2. **Structured Outputs (JSON mode / Tool calling)**: Essential for the `generate_structured` method used by the Answer Safety Gate and Trust Evaluator.
3. **Context Window**: Minimum 8k tokens to handle chunk retrieval limits.
4. **Reliable Infrastructure**: Acceptable uptime and rate limits for fallback routing.

## Selected Candidates

### 1. Groq (Currently Primary/Secondary)
- **Status**: CONFIGURED & VERIFIED
- **Capabilities**: High-speed inference, native structured output, OpenAI compatible.
- **Role**: Essential for fast structured extraction in the RAG pipeline.

### 2. NVIDIA NIM (Currently Primary/Secondary)
- **Status**: CONFIGURED & VERIFIED
- **Capabilities**: High quality models (Nemotron, Llama 3), OpenAI compatible, native structured output.
- **Role**: Primary robust inference for clinical summarization.

### 3. Cloudflare Workers AI
- **Status**: REJECTED FOR STRUCTURED ROUTER (Legacy Adapter)
- **Analysis**: While the free tier (`@cf/meta/llama-4-scout-17b-16e-instruct` etc.) is attractive, the current `CloudflareBackend` adapter in the project is a legacy implementation. It only implements basic text generation (`generate`) and lacks the `generate_structured` capability required by the modern `LiveProviderRouter`. It is therefore **CONFIGURED BUT NOT INTEGRATED**.

### 4. Hugging Face Inference API
- **Status**: REJECTED FOR STRUCTURED ROUTER (Legacy Adapter)
- **Analysis**: Hugging Face provides a robust inference router (`router.huggingface.co/v1`). However, the project's `HuggingFaceBackend` is a legacy adapter lacking structured output parsing required for the safety gates. It is **CONFIGURED BUT NOT INTEGRATED**.

### 5. Other Providers (e.g., Z AI, Mistral Free Tier, FreeLLM)
- **Status**: NOT CONFIGURED
- **Analysis**: Credentials not present in `.env`.

## Conclusion
The live application relies heavily on Pydantic-based structured extraction for its clinical safety gates. Therefore, only **Groq** and **NVIDIA** are currently suitable for the live multi-provider router. Hugging Face and Cloudflare cannot be used in the critical path until their adapters are rewritten to support strict JSON schema enforcement.
