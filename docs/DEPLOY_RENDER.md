# Deploying to Render

The app runs as **one Docker web service**: FastAPI serves the API and the built React frontend from the same URL. `render.yaml` (a Render Blueprint) describes it; `Dockerfile` builds it.

## Before you start

- A Render account (render.com), signed in with GitHub, with access to `sandysunny99/adaptive-trust-medical-rag`.
- A paid instance type. The free 512 MB instance cannot hold the NLI and embedding models; the Blueprint asks for **Standard (2 GB)**. If the service restarts with "out of memory", move it to **Pro (4 GB)**.
- Your API keys at hand (Groq, Cloudflare account ID and token, NVIDIA). They are typed into Render, never committed.

## Steps

1. **Open the Blueprint page.** In the Render dashboard choose **New → Blueprint**.
2. **Connect the repository.** Pick `sandysunny99/adaptive-trust-medical-rag`. Render finds `render.yaml` on the branch named in it (`claude/project-thread-q4qv1f`).
3. **Fill in the secrets.** Render lists every value marked `sync: false`: `GROQ_API_KEY`, `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `NVIDIA_API_KEY`. Paste the same values you have in `.env.local`. The non-secret settings (`LLM_PROVIDER=groq`, `LLM_FALLBACK_PROVIDERS=cloudflare`, `NVIDIA_OCR_MODEL`) are already in the file.
4. **Apply.** Click **Apply** / **Deploy Blueprint**. The first build takes about 10–15 minutes: it builds the frontend, installs CPU-only PyTorch and downloads the two pinned models into the image.
5. **Watch the logs.** In the service's **Logs** tab, wait for:
   - `LLM providers (in order): [{'provider': 'groq', ...}, {'provider': 'cloudflare', ...}]`
   - `Application startup complete.`
   Render marks the service **Live** once `/health/ready` answers.
6. **Open the app.** Use the `https://adaptive-trust-medical-rag-xxxx.onrender.com` URL at the top of the service page. Advanced settings should list Groq and Cloudflare as available.
7. **Smoke test.** Type `lisinopril` and analyse: you should get a cited answer (trust 0.72, R0). `warfarin` + `ibuprofen` should abstain.

## Later changes

- Every push to the branch in `render.yaml` redeploys automatically (`autoDeploy: true`).
- To change a key: service → **Environment** → edit → **Save, rebuild and deploy**.
- To deploy from another branch: edit `branch:` in `render.yaml`, or change it under service → **Settings → Build & Deploy**.

## Troubleshooting

| What you see | Likely cause | Fix |
|---|---|---|
| Build fails at `torch==… --index-url …/cpu` | That torch version has no CPU wheel yet | Pin the nearest CPU version in the Dockerfile's torch line |
| Service restarts, log says "Out of memory" | 2 GB is not enough | Instance type → Pro (4 GB) |
| Models show "Not configured" | A key is missing or misspelt in Environment | Check the four secret names exactly |
| `429 rate_limit_exceeded` | More than 60 requests a minute from one address | Wait a minute; the limit is in `api/middleware.py` |
| First analysis is slow | Models load in the background after start | Wait about 30 s after "Application startup complete" |

Research prototype only: not for clinical use, and use synthetic inputs only.
