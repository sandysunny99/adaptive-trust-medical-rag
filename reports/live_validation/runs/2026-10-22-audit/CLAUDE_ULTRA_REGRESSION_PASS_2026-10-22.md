# Ultra regression pass — 2026-10-22 (afternoon)

Follows `CLAUDE_POST_REMEDIATION_BROWSER_VALIDATION_2026-10-22.md`. Earlier reports are unchanged.
Research tool output only; nothing here is clinical advice. No commit, push, tag, merge, deployment
or approval was made by Claude. REL-LIVE-0003 is still pending and `UNGRADED`.

## 1. The three questions

**Which provider returned "Extra data at line 1, column 159"?** NVIDIA, `meta/llama-3.2-11b-vision-instruct`.
The backend log for both failed requests (`db9bd506…`, `98eb9668…`):
- Request: an uploaded 315,335-byte image (not the synthetic one).
- Reply: HTTP 200 in 5.9 s and 6.7 s, a 321–322-character body.
- Failure: "Extra data" at column 160 and 159.
- Groq was never tried, because a malformed reply (SCHEMA_ERROR) was not a fallback class.

The parser only reaches the "Extra data" branch when the whole reply starts with `{` and ends with `}`,
so the reply was most likely **one JSON object followed by a second one**. This is not confirmed: the
reply was never logged, by design. **It did not reproduce with synthetic images**: 6 of 6 valid
replies across 3 synthetic prescriptions, PNG and noisy JPEG.

**Which revision is the app serving?** Branch `wip/pre-threads-20261022-1440`, HEAD `a96e171` (the user's
checkpoint), plus uncommitted edits. The backend that produced the failures (pid 29672) started at 15:02:48,
after the last source change (15:01:35), so it was running the working tree as it then was.
`ui/3d-redesign` = `origin/ui/3d-redesign` = `30774eb`. `baf6c93` and `30774eb` are ancestors of HEAD.
The strict-JSON parser that raised the error is in `a96e171` (added by the other agent); `30774eb` had
`json.loads` without it.

**Can Groq fallback succeed through the application?** Yes, observed in the browser. The backend was
started with `NVIDIA_OCR_BASE_URL=http://127.0.0.1:9/v1` (an existing setting; no test code in the app) and
received the synthetic image upload:

| Attempt | Provider / model | Result |
|---|---|---|
| 1 | NVIDIA 11b | NETWORK, 2.3 s |
| 2 | NVIDIA 11b (retry) | NETWORK, 2.3 s |
| 3 | `groq_vision` `qwen/qwen3.8-27b` | success, 1.1 s: "Lisinopril 10 mg tablet", "Spironolactone 25 mg tablet", both HIGH |

The SSE event named `groq_vision`. The user confirmed in the UI; RxNorm resolved 29046 and 9997; the
identity gate abstained, 7 of 11 steps, no links. Afterwards the backend was restarted without the override.

## 2. Scope decisions (Ultra pushback)

| Directive item | Decision |
|---|---|
| Repair or salvage malformed JSON | Not done: guessing at a cut-off medication list can drop a drug silently. A malformed reply now goes to the other provider once, otherwise fails closed. |
| Build ID in `/health` and logs | Not done: process start time against file times already tied the runtime to the source. |
| Registry with refresh, staleness, last-verified | Not done. The router remembers models a provider refused (MODEL_NOT_FOUND, AUTH*) until restart; the model list and manual selection read that. NVIDIA's own catalog lists the 404 model, so only a real call can tell. |
| Durable or TTL history | Not needed: history is browser-side (IndexedDB, explicit "Save"). The real leak was the backend pending dict, now fixed. |
| Warm-up readiness UI | Replaced by loading the models at startup in the background (one load, behind a lock): the first event now arrives in 0.3 s, against 21.5 s before. |
| Test-only failure injection in the app | Not added: the existing `NVIDIA_OCR_BASE_URL` setting gave the same proof with nothing that could leak into production. |
| New evidence for sertraline + tramadol | Nothing: the abstention is correct (14 chunks, none names either drug), and existing tests cover it. |

## 3. Changes (uncommitted, on top of `a96e171`)

| File | Change |
|---|---|
| `llm_backend/openai_vision_backend.py` | SCHEMA_ERROR is a fallback class (no same-model retry). On "Extra data" the log names only the shape of the remainder (`json` / `fence` / `text`, and its length), never content. HTTP error bodies go to the server log, not the message. |
| `llm_backend/openai_compatible_backend.py` | Upstream error bodies go to the server log only; the user-facing message keeps class, model and HTTP status. |
| `llm_backend/live_provider_router.py` | `unavailable`: providers that returned MODEL_NOT_FOUND or AUTH*; automatic mode skips them while another remains (marked `shortcut:` until restart). |
| `llm_backend/model_registry.py` | Models of those providers show `is_available: false`; manual selection is refused with the reason. |
| `api/routes/analyze.py` | The stream always drops its pending entry, including the uploaded image. A second stream request gets NOT_FOUND instead of re-running the pipeline. |
| `api/routes/ingest.py` | No ingester: 503 "the document was not ingested" instead of a fabricated success with a poisoning score. |
| `api/app.py` | Background model warm-up at startup (not under `TESTING`). Logging handler and Groq vision fallback from the previous pass. |
| `services/live_application.py` | `_lazy_init_models` behind a lock (one load for concurrent callers); the loader itself is `_load_models`. |
| `frontend/src/components/PrescriptionDropzone.tsx` | Disclosure: the image goes to the configured vision provider and, if that is unavailable, to its backup. Use synthetic or de-identified images. |
| `tests/fixtures/rel_live_0003_candidate/` | Tracked, byte-identical copy of the pending candidate. `test_live_evidence_provenance.py` and `test_live_audit_regressions.py` no longer read the untracked audit folder. |
| Tests | Vision: malformed shapes, malformed→Groq, both malformed, log shape without content, single model load. Router and model list: unavailable memory. `/ingest`: 503, ingester pass-through, 500. Stream: memory released and no re-run. |

## 4. Results

| Check | Kind | Result |
|---|---|---|
| Backend `pytest` (`TESTING=1`) | stand-in NLI, simulated providers | PASSED 1581 |
| Targeted suites (vision, router, API, additional-instructions, provenance, audit regressions) | as above | PASSED 176 |
| Frontend `vitest` / `tsc -b` / lint | jsdom / static | PASSED 123 (19 files) / exit 0 / 3 baseline warnings |
| ruff, Bandit | static | PASSED |
| Synthetic reproduction of the malformed JSON | real NVIDIA | Not reproduced (6/6 valid) |
| Groq fallback through the browser | real browser, real Groq, NVIDIA made unreachable via config | PASSED |
| Startup warm-up | real backend | first SSE event at 0.3 s (21.5 s before) |
| Clean worktree of `a96e171` plus the current changes, no audit folder, no `.env` | full suite | see section 5 |

## 5. Clean-checkout reproducibility

See the addendum below; it is filled in when the run completes.

## 6. Still open

1. The exact content after NVIDIA's first JSON object is unknown. The next occurrence will log its shape;
   the fallback now covers it.
2. REL-LIVE-0003 needs a severity grade and approval; no live evidence-backed answer exists.
3. NVIDIA's text model (404) is marked unusable only after its first failure in each process.

## Addendum: clean-checkout result

A disposable worktree of `a96e171` (at `C:\Users\sunny\cwt-0022`, now removed) had the current uncommitted
changes and the new `tests/fixtures/rel_live_0003_candidate/` applied. It had **no**
`reports/live_validation/runs/` and no `.env` files. pytest ran its own `src` (`pythonpath = ["src"]`),
with `TESTING=1`.

**Result: 1577 passed, 4 skipped, 0 failed.** The 4 skips are the credential-gated live connectivity
tests in `test_provider_connectivity_preflight.py` (GROQ, GEMINI, HF, CLOUDFLARE keys not set), which is
expected without `.env`. **The suite no longer depends on untracked audit files**, provided
`tests/fixtures/rel_live_0003_candidate/` is committed with the rest of these changes.
