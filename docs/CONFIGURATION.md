# Setup and configuration

How to install, configure and run the live application locally. Variable names below are taken from the source code; values are placeholders. Never commit real keys: `.env` and `.env.local` are git-ignored, and a pre-commit hook scans staged changes for secrets.

## Requirements

- Python 3.12 (`requires-python = ">=3.12, <3.13"`), managed with [uv](https://docs.astral.sh/uv/). Do not `pip install` into the system Python.
- Node.js and npm for the frontend (Vite 8, React, TypeScript).
- Network access to the providers you configure and to `rxnav.nlm.nih.gov`. The embedding model (`all-MiniLM-L6-v2`) and the NLI model (`pritamdeka/PubMedBERT-MNLI-MedNLI`) download from Hugging Face on first use.
- PostgreSQL + pgvector is optional and only used by the research harness.

## Install

```bash
uv sync                              # backend dependencies from pyproject.toml / uv.lock
cd frontend && npm install           # frontend dependencies
```

Enable the repository's commit gate once per clone: `git config core.hooksPath .githooks`.

## Environment

The backend reads `.env.local` and then `.env` from the directory it is started in (`python-dotenv`, existing variables are not overridden). Start from the template: `cp .env.example .env`, then fill in only the providers you use.

### Live application

| Variable | Purpose |
|---|---|
| `NVIDIA_LLM_API_KEY` (fallback `NVIDIA_API_KEY`) | NVIDIA answer model |
| `NVIDIA_LLM_MODEL`, `NVIDIA_LLM_BASE_URL` | Optional; default `nvidia/nemotron-3-super-120b-a12b`, `https://integrate.api.nvidia.com/v1` |
| `NVIDIA_OCR_API_KEY` (fallbacks `NVIDIA_VISION_API_KEY`, `NVIDIA_API_KEY`) | Prescription-image vision model; without any of these, image analysis is unavailable |
| `NVIDIA_OCR_MODEL` / `NVIDIA_VISION_MODEL`, `NVIDIA_OCR_BASE_URL` / `NVIDIA_VISION_BASE_URL` | Optional; default `meta/llama-3.2-11b-vision-instruct` on the NVIDIA endpoint |
| `GROQ_API_KEY` | Groq answer model (`openai/gpt-oss-120b`) |
| `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Workers AI answer model (`@cf/meta/llama-3.3-70b-instruct-fp8-fast`, 4096-token limit) |
| `LLM_PROVIDER` | Provider tried first in automatic mode (default `nvidia`) |
| `TESTING` | `1` only for the test suite: stub embeddings, relaxed rate limit. Never set it for a real run |

A provider is offered in the frontend's model list only when its credentials are set and it is registered. Automatic mode tries NVIDIA, Groq, Cloudflare in that order (after `LLM_PROVIDER`) and fails over on errors; a manually selected model does not fail over.

### Research harness and other tools

`GROQ_MODEL`, `HF_TOKEN`, `HF_MODEL`, `HF_FREE_ONLY_MODE`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `CLOUDFLARE_MODEL`, `CLOUDFLARE_ENABLED`, `CLOUDFLARE_FREE_ONLY_MODE`, `FREELLMAPI_API_KEY`, `FREELLMAPI_BASE_URL`, `LLM_MODE`, `LLM_PRIMARY_PROVIDER`, `LLM_TERTIARY_PROVIDER_ENABLED`, `SCIENTIFIC_MODE`, `LLM_SECRET_REDACTION`, `LLM_LOG_RAW_KEYS`, `MLFLOW_TRACKING_URI` are read by `llm_routing/config.py`, `llm_backend/__init__.py`, the annotation engine and the evaluation code, not by the live router. (`HF_TOKEN` and `FREELLMAPI_API_KEY` also add a name to the live priority list, but no live backend is registered for them.)

## Run

```bash
# Backend: http://127.0.0.1:8000 (the package is run from src/, hence --app-dir)
uv run python -m uvicorn --app-dir src adaptive_trust_medical_rag.api.app:app --host 127.0.0.1 --port 8000

# Frontend: http://localhost:5173, proxies /api, /query, /health, /research-state to port 8000
cd frontend && npm run dev
```

- To run a second backend on another port, also point the frontend proxy at it (the targets are set in `frontend/vite.config.ts`).
- The first analysis loads the embedding and NLI models and takes longer.
- `GET /health` returns `"status": "unhealthy", "database": false` when no database is configured; the live pipeline does not need one.
- `GET /api/v1/llm/models` shows which answer models are available.

## Troubleshooting

| Symptom | Likely cause and what to check |
|---|---|
| `LLM_ERROR` "… timeout" | The provider did not answer within the 30 s adapter timeout. In automatic mode the next provider is tried; NVIDIA's answer model frequently times out (open item B-LIVE-NVIDIA-LLM-TIMEOUT). Select another model, or move one first with `LLM_PROVIDER` |
| `LLM_OUTPUT_VALIDATION_FAILURE` | The model's output was not valid JSON for the answer schema. The log records provider, model, finish reason and length (a `length` finish reason means the output was cut off) |
| `VISION_EXTRACTION_ERROR` "…valid JSON" / schema message | The vision model's reply was not a single schema-valid JSON object. Retry; persistent failures mean the provider is returning prose or another format |
| `VISION_EXTRACTION_ERROR` "Vision Provider Timeout" / authentication | Vision endpoint slow or credentials missing/invalid (`NVIDIA_OCR_API_KEY` or fallbacks) |
| Image upload rejected | Only JPEG, PNG and WebP up to 5 MB are accepted |
| `INPUT_REJECTED` | The Additional Instructions contained an instruction aimed at the system, markup or a personal identifier |
| `RETRIEVAL_UNAVAILABLE` | Retrieval failed to initialise; the message names the cause (corpus file missing or unreadable, embedding model could not load) |
| Every interaction analysis abstains | Expected while no relationship record is approved: pairwise claims have no relationship identity |
| Model missing from the dropdown | Its credentials are not set, or the provider is not registered |
| Frontend shows "SSE connection error" after an error | The server closed the stream after the terminal error event; the error itself is shown in the result panel |
| `embedding_mode: "testing_stub"` in the retrieval event | `TESTING=1` is set in the backend environment; unset it |
