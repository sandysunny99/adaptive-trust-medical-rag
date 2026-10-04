# TRACK_A_LLM_MODEL_CANDIDATES_V1

| Provider | Model | Exact Version/Revision | Context Length | Structured JSON Support | Temp Control | Top_P | Seed Support | Max Tokens | Local/External | Resource Requirement | Determinism Considerations | Availability Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Google Gemini | gemini-1.5-flash | gemini-1.5-flash-002 | 1M+ | Yes (Schema) | Yes | Yes | Yes | 8192 | External | API Access | Highly deterministic with T=0 & Seed | Missing Credentials |
| Groq | llama3-8b-8192 | llama3-8b-8192 | 8192 | Yes (JSON mode) | Yes | Yes | Yes | 8192 | External | API Access | Fast, deterministic with T=0 | Missing Credentials |
| Cloudflare | @cf/meta/llama-3-8b-instruct | Latest | 8192 | Yes | Yes | Yes | No | 2048 | External | API Access | Lacks strict seed control | Missing Credentials |
| HuggingFace | meta-llama/Meta-Llama-3-8B-Instruct | main | 8192 | Yes | Yes | Yes | Yes | 8192 | External | API Access | Deterministic with T=0 | Missing Credentials |
| Local CPU (llama.cpp) | Meta-Llama-3-8B-Instruct.Q4_K_M.gguf | Q4_K_M | 8192 | Yes (Grammar) | Yes | Yes | Yes | 2048 | Local | 6GB RAM, modern CPU | Fully deterministic, but execution will be slow (2-5 tok/s) | Model not downloaded |

*Note: CPU-only execution is possible via llama.cpp python bindings for Q4 quantized models, providing a completely offline research control. Execution for 50 records * 2 passes would take approximately 30-60 minutes.*
