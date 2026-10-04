# TRACK_A_LLM_BACKEND_DISCOVERY_V1

## Discovered LLM Backends

| Backend | Implementation Path | Provider Type | Local/External | Required Dependencies | Authentication Requirement | Model Configured | Usable Offline | Reproducibility Settings | Status |
|---|---|---|---|---|---|---|---|---|---|
| Cloudflare | src/adaptive_trust_medical_rag/llm_backend/cloudflare_backend.py | Cloudflare Workers AI | External | 
equests, iohttp | CLOUDFLARE_API_KEY | None | No | Yes (temp, max_tokens) | INACTIVE (Missing Auth) |
| Google Gemini | src/adaptive_trust_medical_rag/llm_backend/google_gemini_backend.py | Google AI | External | google-genai | GEMINI_API_KEY | None | No | Yes (temp, top_p, seed) | INACTIVE (Missing Auth) |
| Groq | src/adaptive_trust_medical_rag/llm_backend/groq_backend.py | Groq API | External | 
equests, iohttp | GROQ_API_KEY | None | No | Yes (temp, seed) | INACTIVE (Missing Auth) |
| HuggingFace | src/adaptive_trust_medical_rag/llm_backend/huggingface_backend.py | HuggingFace Inference API / Local | External/Local | huggingface_hub, 	ransformers | HUGGINGFACE_API_KEY | None | Yes (if local) | Yes (seed, temp) | INACTIVE (Missing Auth/Models) |
| Mock | src/adaptive_trust_medical_rag/llm_backend/mock_backend.py | Hardcoded Responses | Local | None | None | None | Yes | N/A | INVALID FOR RESEARCH |

## Environment Inspection
* OPENAI_API_KEY: ABSENT
* GEMINI_API_KEY: ABSENT
* GROQ_API_KEY: ABSENT
* ANTHROPIC_API_KEY: ABSENT
* CLOUDFLARE_API_KEY: ABSENT
* HUGGINGFACE_API_KEY: ABSENT
