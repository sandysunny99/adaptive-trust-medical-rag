# One container: the FastAPI backend also serves the built React frontend.
# Build:  docker build -t medical-rag .     Run:  docker run -p 8000:8000 --env-file .env.local medical-rag

# ── 1. Frontend build ────────────────────────────────────────────────────────
FROM node:22-slim AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ── 2. Backend runtime ───────────────────────────────────────────────────────
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    HF_HOME=/app/.hf-cache
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /usr/local/bin/uv
WORKDIR /app

# Dependencies from uv.lock, but torch from the CPU index: the locked CUDA build adds several GB
# of nvidia-* wheels and the host has no GPU.
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev --no-hashes --no-emit-project -o /tmp/req.txt \
 && grep -vE '^(torch|triton|nvidia-)' /tmp/req.txt > /tmp/req-cpu.txt \
 && uv venv /app/.venv \
 && uv pip install --no-deps -r /tmp/req-cpu.txt \
 && TORCH=$(sed -n 's/^torch==\([^ ;]*\).*/\1/p' /tmp/req.txt) \
 && uv pip install --no-deps "torch==${TORCH}" --index-url https://download.pytorch.org/whl/cpu \
 && rm -rf /root/.cache

# Bake the pinned models into the image, so a restart does not download them again.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2'); \
from huggingface_hub import snapshot_download; \
snapshot_download('pritamdeka/PubMedBERT-MNLI-MedNLI', revision='f1b6ce2e0d49f295b4cbcdc56c01b5fab6d068ab')"

COPY src ./src
COPY config ./config
COPY data ./data
COPY --from=web /web/dist ./frontend/dist

RUN useradd --create-home app && chown -R app /app
USER app
EXPOSE 8000
# --proxy-headers: behind Render's proxy, use the caller's address (rate limit, logs).
CMD uvicorn --app-dir src adaptive_trust_medical_rag.api.app:app --host 0.0.0.0 --port ${PORT:-8000} \
    --proxy-headers --forwarded-allow-ips '*'
