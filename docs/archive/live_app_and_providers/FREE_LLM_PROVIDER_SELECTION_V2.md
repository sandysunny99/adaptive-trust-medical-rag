# Free LLM Provider Selection V2

## Overview
This document evaluates candidates from wesome-free-llm-apis for integration as the **tertiary fallback provider** in the Live Multi-Provider Router.

## Candidate Evaluation

| Provider | API / Endpoint | Model | OpenAI Compatible | Structured Output (JSON Schema) | Context | Free Tier | Status |
|---|---|---|---|---|---|---|---|
| **Groq** | pi.groq.com/openai/v1 | gpt-oss-120b | Yes | Yes (Native) | 128k | High limit | PRIMARY |
| **NVIDIA NIM** | integrate.api.nvidia.com/v1 | 
emotron-3-super-120b-a12b | Yes | Yes (Native) | 128k | High limit | SECONDARY |
| **Cloudflare Workers AI** | pi.cloudflare.com/.../v1 | @cf/meta/llama-3.3-70b-instruct-fp8-fast | Yes | Yes (Native) | 8k+ | 10k Neurons/day | SELECTED (Tertiary) |
| **Hugging Face** | pi-inference.huggingface.co/models/.../v1 | meta-llama/Llama-3.3-70B-Instruct | Yes | Variable/Fails | 8k | Strict limits | INCOMPATIBLE |
| **Google Gemini** | generativelanguage.googleapis.com/v1beta/openai | gemini-1.5-flash | Yes | Yes | 1M+ | Yes | Missing Credential |
| **Mistral** | pi.mistral.ai/v1 | mistral-large-latest | Yes | Yes | 128k | Yes | Missing Credential |
| **Z AI / FreeLLM** | Various | Unknown | Varies | Varies | Varies | Unknown | Missing Credential |

## Conclusion
The wesome-free-llm-apis repository is a directory, not a single API. Based on current environment credentials and native OpenAI structured JSON support, **Cloudflare Workers AI** has been selected as the optimal tertiary provider.
