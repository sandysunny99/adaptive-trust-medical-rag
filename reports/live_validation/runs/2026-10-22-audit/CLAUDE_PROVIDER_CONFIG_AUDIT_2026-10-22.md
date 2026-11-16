# Provider configuration and credential-consumer audit — 2026-10-22

Earlier reports are unchanged. No secret value appears here.

**Confirmations:**
- `.env.local` was **not modified**: last write 2026-10-22 11:27, before this session's edits. An attempt
  to copy it was blocked by a deny rule and was not worked around.
- No credential was deleted, replaced or revoked.
- No commit, push, tag, merge or deployment was made by Claude.
- `baf6c93` and `30774eb` are intact; HEAD is `a96e171` on `wip/pre-threads-20261022-1440`, plus
  uncommitted changes.
- REL-LIVE-0003 is pending and `UNGRADED`; the frozen corpus is unchanged.

## 1. Baseline

| Item | Value |
|---|---|
| Source | `a96e171` plus uncommitted edits (20 tracked files, `tests/fixtures/rel_live_0003_candidate/` untracked) |
| Backend | 127.0.0.1:8000, started from this session with process override `LLM_FALLBACK_PROVIDERS=cloudflare` |
| Frontend | Vite at 127.0.0.1:5173 |
| Text LLM order (startup log) | groq `openai/gpt-oss-120b` → cloudflare `@cf/meta/llama-3.3-70b-instruct-fp8-fast` |
| Vision (startup log) | nvidia_vision `meta/llama-3.2-11b-vision-instruct` → groq_vision `qwen/qwen3.8-27b` |
| `start_servers.cmd` | Starts uvicorn and Vite with `TESTING` cleared; **sets no provider variables**, so without the `.env.local` line below the order is groq → nvidia → cloudflare |

## 2. Who reads each variable

Code reads only (`os.environ.get`, `os.getenv`, `_env_float`, `${VAR}`), across all tracked files. Comments
and documentation are not counted.

| Variable | Live app | Research and other readers | Verified behaviour (today) | Status |
|---|---|---|---|---|
| `GROQ_API_KEY` | text provider, vision backup | annotation engine, research LLM registry, scripts | 200: models list and `gpt-oss-120b` chat | active |
| `GROQ_MODEL` | yes | research config | `openai/gpt-oss-120b` works | active |
| `GROQ_VISION_MODEL` | yes (default `qwen/qwen3.8-27b`) | — | real extraction through the app (browser, your upload) | active |
| `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` | text provider | research registry, pilot adapter, scripts | Workers AI chat 200 (exact app endpoint); generic token-verify 401 is a scope matter | active |
| `CLOUDFLARE_MODEL` | **now read** (was hard-coded; same default) | research config | — | active |
| `NVIDIA_OCR_API_KEY`, `NVIDIA_OCR_MODEL`, `NVIDIA_OCR_BASE_URL` | primary vision | — | valid; NVIDIA vision intermittently stalls with both NVIDIA keys | active |
| `NVIDIA_API_KEY` | NVIDIA text provider; fallback key for LLM and OCR | annotation engine, scripts | valid key; `nemotron-3-super-120b` returns 404 "not found for account" | active key, unusable model |
| `NVIDIA_LLM_*`, `NVIDIA_VISION_*`, `GROQ_BASE_URL`, `VISION_FALLBACK_MODEL`, `*_TIMEOUT_S`, `VISION_DEADLINE_S`, `LLM_REQUEST_DEADLINE_S` | yes (optional) | — | defaults in use | optional |
| `LLM_PROVIDER` | yes (primary) | proof scripts | `.env.local` = groq wins over `.env` = nvidia | active |
| `LLM_FALLBACK_PROVIDERS` | yes (canonical fallback list) | — | **not in `.env.local`** | needs your edit (section 4) |
| `LLM_FAILOVER_ENABLED` | yes | — | true | active |
| `LLM_PRIMARY_PROVIDER` | only if `LLM_PROVIDER` is unset | research registry | — | research (shadowed live) |
| `LLM_FALLBACK_PROVIDER` (singular) | warned, not used | — | `gemini`; no live adapter | research-only |
| `CLOUDFLARE_ENABLED` | warned, not used | research config | `false` would *remove* the wanted fallback if honoured | research-only |
| `LLM_TERTIARY_PROVIDER_ENABLED`, `LLM_SECRET_REDACTION`, `LLM_LOG_RAW_KEYS`, `CLOUDFLARE_FREE_ONLY_MODE`, `HF_FREE_ONLY_MODE` | no | research config | — | research-only |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | no | annotation engine, `phase15_runner.py`, research registry, `proof_a/b.py`, `pi_statin_eval_v2.py`, preflight test | **key rejected (400)** | research-only, broken |
| `HF_TOKEN`, `HF_MODEL` | no (deliberately unregistered) | research registry, `gen_final_v6-8.py`, root scripts, preflight test | **token rejected (401)** | research-only, broken |
| `PHASE15_FAILOVER_ENABLED` | no | **no code reads it** | — | stale |
| `PORT`, `HOST`, `WORKERS`, `ALLOWED_ORIGINS`, `MAX_UPLOAD_SIZE_MB`, `LOG_LEVEL` (in the old `.env.example`) | no | **no code reads them** (CORS and the 5 MB limit are fixed in code) | — | removed from the template |

**Gemini and Hugging Face:**
- Not needed by the live app.
- They **are** needed by research workflows, and those currently fail auth: the annotation engine and
  phase 15 runner with Gemini, and the research registry and generation scripts with HF.
- Recommendation: keep both variables. Replace the keys if you will rerun those workflows; otherwise
  leave them (they affect nothing live). Removing them would turn an auth error into a missing-key
  error, with no other change.

## 3. Changes this pass

| File | Change | Why |
|---|---|---|
| `api/app.py` | Cloudflare model from `CLOUDFLARE_MODEL` (same default) | the setting existed but was silently ignored |
| `.env.example` | Rewritten to list only variables the code reads, grouped live vs research-only, placeholders only | it advertised six unread settings (including a wrong 10 MB upload limit) and lacked the live routing and vision settings |
| `tests/test_live_provider_failover_policy.py` | Cloudflare model test | covers the above |

**Not done (Ultra):**
- No alias between `LLM_FALLBACK_PROVIDER` and `..._PROVIDERS`: one canonical name, and the warning
  already says so.
- `CLOUDFLARE_ENABLED` not honoured, for the reason in section 2.
- No provider order hard-coded into `start_servers.cmd`: the configuration stays in one place.
- Provider API checks not repeated: they were run earlier today against the same keys and endpoints.

## 4. The one manual change you need to make

Add this non-secret line to `.env.local`:

```
LLM_FALLBACK_PROVIDERS=cloudflare
```

Effect: the live text LLM order becomes groq → cloudflare, so NVIDIA's 404 text model is never called
automatically. Until then, servers started with `start_servers.cmd` use groq → nvidia → cloudflare. The
router still marks NVIDIA unusable after its first 404 in each process.

## 5. Screenshot check (warfarin + ibuprofen), real backend over HTTP/SSE

| Item | Value |
|---|---|
| RxNorm | warfarin 11289, ibuprofen 5640, both `seed_cache` |
| Retrieval | 14 of a 14-chunk corpus (`top_k=20`), real embeddings |
| Exclusions | 12 unrelated; 2 rejected: SPL-WARFARIN-001 and SPL-IBUPROFEN-001, placeholders, no URL sent |
| Trust | `null` / `NO_ELIGIBLE_EVIDENCE` |
| Security checks | injection ALLOW, poisoning ALLOW; the UI shows Evidence Integrity separately as FLAG |
| Outcome | abstention; the generating stage was never reached (no LLM call) |

This matches the screenshot. The behaviour is correct and was not changed.

## 6. Results

| Check | Result |
|---|---|
| `TESTING=1 uv run pytest -q` (stand-in NLI, simulated providers) | PASSED 1582 |
| Config and API tests | PASSED 70 |
| ruff / Bandit | PASSED / exit 0 |
| gitleaks: uncommitted diff | no leaks |
| gitleaks: directory scan (meant to cover `.env.example` and the new fixture; it covered the whole folder) | no leaks |
| Warfarin + ibuprofen HTTP/SSE | as section 5 |
| Live provider checks | reused from earlier today (not repeated) |
