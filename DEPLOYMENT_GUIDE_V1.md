# Adaptive Trust-Aware Medical RAG - Deployment Guide

**VERSION:** 1.0 (Research / Demonstration Prototype)
**WARNING:** This system is a research/demo prototype for evidence-grounded pharmacology/medical RAG. It is NOT a clinical decision maker, a prescribing system, a dosage recommendation engine, a substitute for a physician/pharmacist, or evidence of clinical validation.

## 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- `uv` Python package manager
- Redis (Optional, for persistent session state)

## 2. Environment Variables
Copy `.env.example` to `.env` in the root directory.
Ensure `GROQ_API_KEY` and `NVIDIA_API_KEY` are populated if using live providers.
DO NOT commit `.env` to version control.

## 3. Backend Startup
The backend utilizes FastAPI and Uvicorn.
```bash
# Install dependencies
uv sync

# Start the application
uv run uvicorn adaptive_trust_medical_rag.api.app:app --host 0.0.0.0 --port 8000
```
Upon startup, the backend automatically initializes the `HybridRetrievalEngine` by loading the frozen `all-MiniLM-L6-v2` embedding model and the `LIVE_MEDICAL_CORPUS_V2` evidence chunks.

## 4. Frontend Startup and Production Build
The frontend is a React + Vite application.
```bash
cd frontend
npm install
npm run build
```
The output is generated in `frontend/dist`. You can serve this via Nginx, Vercel, or any static hosting solution.
API keys are explicitly excluded from the Vite bundle.

## 5. Health and Readiness Checks
- **Readiness/Health:** Available at `GET /health` (returns DB status and API uptime).

## 6. Provider Setup and Failure Handling
Providers (Groq, NVIDIA) are routed dynamically based on environment configuration. 
In the event of an API timeout or 5xx error, the application yields a controlled HTTP error back to the client. Failover does not bypass evidence/safety gates.

## 7. Security Considerations
- **CORS:** Must be restricted to trusted frontend origins via `ALLOWED_ORIGINS`.
- **Upload Limits:** Prescription images max out at 10MB.
- **Request Isolation:** All analysis requests are scoped to process-local UUID `analysis_store` states. 
- **Temporary Files:** Image bytes are processed entirely in-memory and explicitly purged after vision extraction completes.

## 8. Known Limitations
- The application currently uses process-local memory for request states (`app.state.analysis_store`). Horizontal scaling (e.g., Kubernetes replicas) requires migrating this to Redis.
- Live Corpus is statically loaded from JSON for rapid prototyping; deploying to production scale requires vector database migration (e.g., pgvector).
