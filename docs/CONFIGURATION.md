# Setup and configuration

How to install, configure and run the live application locally. Variable names below are taken from the source code; values are placeholders. Never commit real keys: `.env` and `.env.local` are git-ignored, and a pre-commit hook scans staged changes for secrets.

## Requirements

- Python 3.12 (`requires-python = ">=3.12, <3.13"`), managed with [uv](https://docs.astral.sh/uv/). Do not `pip install` into the system Python.
- Node.js and npm for the frontend (Vite 8, React, TypeScript).
- Network access to the providers you configure and to `rxnav.nlm.nih.gov`. The embedding model (`all-MiniLM-L6-v2`) and the NLI model (`pritamdeka/PubMedBERT-MNLI-MedNLI`) download from Hugging Face on first use.
- PostgreSQL + pgvector is optional and only used by the research harness.
- **Prescription images need a Windows server.** The image text is read locally by the built-in Windows OCR engine (`Windows.Media.Ocr`, through `powershell.exe`, with an OCR language installed in the user profile); nothing extra is installed. On Linux or macOS, or when the engine cannot start, every image request ends with `IMAGE_TEXT_UNVERIFIABLE` and the image is never sent to a provider. Analysis of typed drug names works on any platform.

## Install

```bash
uv sync                              # backend dependencies from pyproject.toml / uv.lock
cd frontend && npm install           # frontend dependencies
```

Enable the repository's commit gate once per clone: `git config core.hooksPath .githooks`.

## Environment

The backend reads `.env.local` and then `.env` from the repository root, whatever the directory it is started in (`python-dotenv`). Precedence, highest first: the process environment, `.env.local`, `.env`, the defaults in `api/app.py`; a file never overrides a value already set, and values are never logged. Start from the template: `cp .env.example .env.local`, then fill in only the providers you use.

### Live application

| Variable | Purpose |
|---|---|
| `NVIDIA_LLM_API_KEY` (fallback `NVIDIA_API_KEY`) | NVIDIA answer model |
| `NVIDIA_LLM_MODEL`, `NVIDIA_LLM_BASE_URL` | Optional; default `nvidia/nemotron-3-super-120b-a12b`, `https://integrate.api.nvidia.com/v1` |
| `NVIDIA_OCR_API_KEY` (fallbacks `NVIDIA_VISION_API_KEY`, `NVIDIA_API_KEY`) | Prescription-image vision model; without any of these, image analysis is unavailable |
| `NVIDIA_OCR_MODEL` / `NVIDIA_VISION_MODEL`, `NVIDIA_OCR_BASE_URL` / `NVIDIA_VISION_BASE_URL` | Optional; default `meta/llama-3.2-11b-vision-instruct` on the NVIDIA endpoint |
| `VISION_FALLBACK_MODEL` | Optional second NVIDIA vision model, tried after the first fails on availability or output format; unset by default |
| `GROQ_VISION_MODEL` | Groq vision fallback, tried last (needs `GROQ_API_KEY` and an NVIDIA vision key); default `qwen/qwen3.8-27b`; an empty value disables it |
| `VISION_TIMEOUT_S`, `VISION_DEADLINE_S` | Per-attempt timeout (default 30) and total deadline for all vision attempts (default 75), in seconds; a non-number or a value ≤ 0 keeps the default |
| `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_BASE_URL` | Groq answer model (default `openai/gpt-oss-120b`) and the Groq vision fallback |
| `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_MODEL` | Cloudflare Workers AI answer model (default `@cf/meta/llama-3.3-70b-instruct-fp8-fast`, 4096-token limit) |
| `LLM_PROVIDER` (fallback `LLM_PRIMARY_PROVIDER`) | Provider tried first in automatic mode (default `nvidia`) |
| `LLM_FALLBACK_PROVIDERS` | Comma-separated providers allowed after the first; unset means every provider with credentials |
| `LLM_FAILOVER_ENABLED` | `false` keeps only the first provider |
| `GROQ_TIMEOUT_S`, `NVIDIA_LLM_TIMEOUT_S`, `CLOUDFLARE_TIMEOUT_S`; `LLM_REQUEST_DEADLINE_S` | Per-request timeout of each answer provider (default 30) and the total deadline across failover (default 120), in seconds |
| `WEB_CONCURRENCY` | Read only to refuse more than one worker (see Run) |
| `TESTING` | `1` only for the test suite: stub embeddings, mock NLI, a 2 s confirmation wait, relaxed rate limit. Never set it for a real run |

A provider is offered in the frontend's model list only when its credentials are set and it is registered. Automatic mode tries NVIDIA, Groq, Cloudflare in that order (after `LLM_PROVIDER`, restricted by `LLM_FALLBACK_PROVIDERS`) and fails over on errors; a manually selected model does not fail over. The startup log lists the provider order; it warns when `LLM_FALLBACK_PROVIDER` (singular) or `CLOUDFLARE_ENABLED=false` is set, because the live router reads neither.

### Research harness and other tools

`HF_TOKEN`, `HF_MODEL`, `HF_FREE_ONLY_MODE`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `CLOUDFLARE_ENABLED`, `CLOUDFLARE_FREE_ONLY_MODE`, `FREELLMAPI_API_KEY`, `FREELLMAPI_BASE_URL`, `LLM_MODE`, `LLM_FALLBACK_PROVIDER`, `LLM_TERTIARY_PROVIDER_ENABLED`, `SCIENTIFIC_MODE`, `LLM_SECRET_REDACTION`, `LLM_LOG_RAW_KEYS`, `MLFLOW_TRACKING_URI` are read by `llm_routing/config.py`, `llm_backend/__init__.py`, the annotation engine and the evaluation code, not by the live router. No live backend is registered for Hugging Face, Gemini or FreeLLMAPI.

## Run

```bash
# Backend: http://127.0.0.1:8000 (the package is run from src/, hence --app-dir)
# One worker only: requests live in process memory; the API refuses to start with more.
uv run python -m uvicorn --app-dir src adaptive_trust_medical_rag.api.app:app --host 127.0.0.1 --port 8000 --workers 1

# Frontend: http://localhost:5173, proxies /api, /query, /health, /research-state to port 8000
cd frontend && npm run dev
```

- **One worker only.** Requests, uploaded images included, live in the process's memory until their stream ends, so the upload, its stream, its confirmation and its cancel must reach the same process. Startup fails with "supports one worker" when `--workers` or `WEB_CONCURRENCY` is above 1. A programmatic `uvicorn.run(..., workers=N)` is not detected; use the command above.
- To run a second backend on another port, point a second frontend dev server at it: `VITE_API_PROXY_TARGET=http://localhost:8001 npm run dev -- --port 5174` (default target `http://localhost:8000`, `frontend/vite.config.ts`).
- The embedding and NLI models start loading in the background at startup; an analysis that arrives first waits for them.
- Timing: a submitted request's stream must open within 120 s; the OCR step has 30 s, the vision step `VISION_DEADLINE_S`, and the confirmation wait 300 s. A cancel or a closed page stops the running step (the OCR process is killed, a vision request is closed) and waits at most 5 s for it. It cannot make a provider stop work it has already received.
- `GET /health` returns `"status": "unhealthy", "database": false` when no database is configured; the live pipeline does not need one.
- `GET /api/v1/llm/models` shows which answer models are available.

## Troubleshooting

| Symptom | Likely cause and what to check |
|---|---|
| `LLM_ERROR` "… timeout" | The provider did not answer within the 30 s adapter timeout. In automatic mode the next provider is tried; NVIDIA's answer model frequently times out (open item B-LIVE-NVIDIA-LLM-TIMEOUT). Select another model, or move one first with `LLM_PROVIDER` |
| `LLM_OUTPUT_VALIDATION_FAILURE` | The model's output was not valid JSON for the answer schema. The log records provider, model, finish reason and length (a `length` finish reason means the output was cut off) |
| `VISION_EXTRACTION_ERROR` "…valid JSON" / schema message | The vision model's reply was not a single schema-valid JSON object. Retry; persistent failures mean the provider is returning prose or another format |
| `VISION_EXTRACTION_ERROR` timeout / deadline / authentication | Vision endpoint slow or credentials missing/invalid (`NVIDIA_OCR_API_KEY` or fallbacks). `failure_class` and `vision_attempts` in the error list each attempt; the log has provider, HTTP status, category and the error body's length only |
| `IMAGE_TEXT_UNVERIFIABLE` | `ocr_status: UNAVAILABLE`: the server is not Windows or the OCR engine could not start; enter names manually. `ERROR`: the read failed or timed out; retry. The image was not sent anywhere |
| `NO_VERIFIED_MEDICATIONS` | The OCR found no text, or none of the vision model's names appears in the OCR text (`suggested` gives how many it proposed). Use a clearer image or enter names |
| `PROVIDER_CONFIGURATION_REQUIRED` on an image | No vision key is set (`NVIDIA_OCR_API_KEY`, `NVIDIA_VISION_API_KEY` or `NVIDIA_API_KEY`) |
| `CONFIRMATION_TIMEOUT` | The medications were not confirmed within 300 s; upload again |
| `ANALYSIS_CANCELLED` | The user cancelled, or the page closed the stream, before confirmation; nothing was analysed |
| `REQUEST_EXPIRED` / `NOT_FOUND` on the stream | The stream opened more than 120 s after submission, or the id is unknown or has already ended (every stream end drops its request) |
| Startup error "supports one worker" | Start with `--workers 1` and unset `WEB_CONCURRENCY` |
| Image upload rejected | Only JPEG, PNG and WebP up to 5 MB are accepted |
| `INPUT_REJECTED` | The Additional Instructions contained an instruction aimed at the system, markup or a personal identifier |
| `RETRIEVAL_UNAVAILABLE` | Retrieval failed to initialise; the message names the cause (corpus file missing or unreadable, embedding model could not load) |
| Every interaction analysis abstains | Expected while no relationship record is approved: pairwise claims have no relationship identity |
| Model missing from the dropdown | Its credentials are not set, or the provider is not registered |
| Frontend shows "SSE connection error" after an error | The server closed the stream after the terminal error event; the error itself is shown in the result panel |
| `embedding_mode: "testing_stub"` in the retrieval event | `TESTING=1` is set in the backend environment; unset it |
