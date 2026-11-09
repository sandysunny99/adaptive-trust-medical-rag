# Adaptive Trust-Aware Medical RAG - Deployment Checklist

## Pre-Deployment
- [ ] `.env` created on deployment host (do not commit to Git).
- [ ] `GROQ_API_KEY` and `NVIDIA_API_KEY` securely populated.
- [ ] `ALLOWED_ORIGINS` strictly defined to match production frontend URL.
- [ ] `LOG_LEVEL` set to `INFO` or `WARNING` to prevent debug leakage.
- [ ] Secret scan verified clean.

## Build and Initialization
- [ ] Backend dependencies synchronized via `uv sync --no-dev`.
- [ ] Frontend built via `npm run build` and statically served.
- [ ] Initial application startup correctly loads `LIVE_MEDICAL_CORPUS_V2.json`.
- [ ] Embedding model successfully cached at initialization without timeout.

## Runtime Validation
- [ ] `GET /health` endpoint returns `status: ok` or `degraded` cleanly.
- [ ] Process memory consumption stable after loading the evidence corpus.
- [ ] Log output is structured and devoid of full patient context / raw query details.

## Functional Smoke Tests
- [ ] **Direct Text Smoke Test**: Submitting direct text (e.g., Warfarin + Aspirin) returns valid safety-gated output.
- [ ] **Multimodal Smoke Test**: Uploading a prescription image extracts text, triggers confirmation, and completes SSE workflow.
- [ ] **Patient Context Isolation Test**: Verified that explicit context (e.g. renal failure) correctly reflects in the output without being inferred from unrelated drug uploads.
- [ ] **Security Boundary Test**: Oversized uploads > 10MB are explicitly rejected with a 400 response.

## Formal Statement
- [ ] Application clearly displays: "RESEARCH OUTPUT ONLY. Not reviewed by clinicians. Not for clinical use."
