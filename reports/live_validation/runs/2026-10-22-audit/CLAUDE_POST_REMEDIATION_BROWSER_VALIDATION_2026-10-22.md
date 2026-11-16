# Post-remediation browser validation — 2026-10-22

This follows `CLAUDE_REMEDIATION_REPORT_2026-10-22.md`, which is unchanged. It closes that report's open
browser check and records what changed since. Research tool output only; nothing here is clinical advice.

No commit, push, tag, merge, deployment or approval was made by Claude. REL-LIVE-0003 is still
pending and `UNGRADED`. No food-guidance evidence exists or was activated.

## 1. Repository state

| Item | Start of this pass | End |
|---|---|---|
| Branch | `ui/3d-redesign` | `wip/pre-threads-20261022-1440` |
| HEAD | `30774eb` | `a96e171` |
| `baf6c93` / `30774eb` | intact | intact, both ancestors of `a96e171`; `ui/3d-redesign` still points at `30774eb` |

`a96e171` ("chore: checkpoint existing work before threads UI", 50 files) was committed at 14:46 by
`sandysunny99` on the new branch `wip/pre-threads-20261022-1440` **while this pass was running. Claude
did not make this commit.** It contains the remediation code and tests. It does **not** contain the
untracked `reports/live_validation/runs/` folder, so tests in that commit read REL-LIVE-0003 from
`reports/live_validation/runs/2026-10-22-audit/rel_live_0003_candidate/`, which the commit lacks. A fresh
checkout of `a96e171` fails `test_live_evidence_provenance.py` and parts of `test_live_audit_regressions.py`
until that folder is committed or the tests point elsewhere.

Uncommitted at the end:
- `src/adaptive_trust_medical_rag/api/app.py` (+9 lines, see 3.4): Claude's.
- `.env.example` and `experiments/runs/live-smoke-v1/*`: earlier, not Claude's; left alone.
- Untracked folders as before.

No other Claude session was running.

## 2. Servers

There were no listeners on 8000 or 5173 at the start. Claude started both with the same commands as
`start_servers.cmd` (repository root, project venv, `TESTING` cleared), in background shells, so their
logs could be read.

| Port | Process | Notes |
|---|---|---|
| 127.0.0.1:8000 | uvicorn, current source | Restarted once to load the logging fix (3.4) |
| 127.0.0.1:5173 | Vite, `--host 127.0.0.1` | Proxies `/api` and `/health` to the backend above (checked through the proxy) |

**Finding:** `start_servers.cmd` ran `npm run dev -- --port 5173` without `--host`. On this machine Vite
then listened only on `::1`, so **http://127.0.0.1:5173 refused connections** (http://localhost:5173
worked). Fixed by adding `--host 127.0.0.1` to the script (one flag).

Effective configuration, from the backend startup log (no secrets):
- LLM order: **groq `openai/gpt-oss-120b` → nvidia `nvidia/nemotron-3-super-120b-a12b` → cloudflare
  `@cf/meta/llama-3.3-70b-instruct-fp8-fast`**, request deadline 120 s.
- Vision: `nvidia_vision`, `meta/llama-3.2-11b-vision-instruct`, no fallback; 30 s per attempt, one
  retry, 75 s total.
- Startup warnings: `LLM_FALLBACK_PROVIDER=gemini` and `CLOUDFLARE_ENABLED=false` are not read.

## 3. Browser results (built-in browser at http://127.0.0.1:5173, real backend, real providers)

### 3.1 Scenario 1: manual entry, lisinopril + spironolactone (PASSED)

- Stages: Input Processing, RxNorm, Evidence Retrieval, Trust Evaluation and Security Checks completed.
  **Medication Extraction and User Confirmation read "Not applicable".** Relationship Verification, LLM
  Analysis, Claim Verification and Safety Gate read "Not run". The summary reads "5 of 9 steps completed".
  Screenshot: `claude_remediation_artifacts/browser_manual_entry_pipeline_stages.jpg`.
- Cards: "Identity resolved". Lisinopril RxCUI 29046 "Curated local mapping"; spironolactone 9997
  "RxNorm exact match". Each says "Drug identity only. Interactions and evidence are verified separately below."
- Trust score: **"Not computed (no eligible evidence)"**, threshold 0.60, R2 with its basis. "11 retrieved
  chunk(s) named none of these medications" and "3 … had no verified source identity".
- Abstention with the evidence-limitation reason. No model call. Evidence & Sources (0).
- Excluded sources (3): SPL-LISINOPRIL-001 and SPL-LISINOPRIL-002 (placeholder) and PMID-31234567 (shared),
  each labelled "Source rejected". **The page contains no external link at all.**
- The first request after startup spent about 20 s loading the embedding and NLI models, with "Input
  Processing (in progress)" shown and no explanation (see 6).

### 3.2 Scenario 2: synthetic prescription image, success (PASSED)

The file was put into the page's real file input through `DataTransfer`. The built-in browser has no OS
file picker; the upload component and the request are the normal ones.

- NVIDIA vision extracted Lisinopril and Spironolactone (HIGH, DETECTED, "Source: Image"). Extraction
  completed between 14.7 s and 27.4 s after submit; the attempt count was not recorded for this run.
- **While waiting, User Confirmation read "(in progress)", not completed.** After "Confirm Medications &
  Analyze" (`POST …/confirm` 200) the backend resumed. The run ended "7 of 11 steps completed" with the
  same identity-gate abstention. No model answer, no links.

### 3.3 Scenario 3: vision failure (PASSED; a real outage, not injected)

The next image run met an **actual NVIDIA stall**. Recorded SSE events
(`claude_remediation_artifacts/browser_sse_vision_timeout_run.json`):

| t (s) | Event |
|---|---|
| 21.5 | `extracting: running` (the 21.5 s before it were model loading after the restart) |
| 81.9 | `extracting: failed` |
| 81.9 | `error VISION_EXTRACTION_ERROR`, attempts: TIMEOUT 30.5 s, then TIMEOUT 30.3 s on the same model |

UI (screenshot `browser_vision_timeout_pipeline_stages.jpg`):
- **Medication Extraction failed; User Confirmation "Not run" (the original green-confirmation bug does
  not occur); every later stage "Not run".**
- No candidates, no medications, no answer.
- Message: "Vision Provider Timeout: model 'meta/llama-3.2-11b-vision-instruct' did not answer within 30 s
  (after 2 attempts in 61 s) Retry the upload, or enter the medication names manually."

Follow-up probes at that time, direct and synthetic image only:

| Model | Result |
|---|---|
| `meta/llama-3.2-11b-vision-instruct` | 3 of 3 timed out at 45 s |
| `meta/llama-3.2-90b-vision-instruct` | 2 attempts timed out (61 s) |
| `microsoft/phi-3-vision-128k-instruct` | 404 "not available to this account" |
| Groq `qwen/qwen3.8-27b`, through the app's own vision adapter and strict parser | **both drugs correct (HIGH) in 1.7 s, 1 attempt** |

### 3.4 Logging fix (new code change)

uvicorn configures only its own loggers, so the package's INFO diagnostics (provider order, per-request
vision timing and `nvcf-reqid`) never reached the server console. `app.py` now adds a stream handler to the
`adaptive_trust_medical_rag` logger at INFO (records still propagate, so pytest `caplog` is unaffected).
Full backend suite after the change: 1565 passed.

### 3.5 Citations

- **C1, live abstention:** no link is rendered for any rejected or excluded source (3.1).
- **C2, isolated fixture:** a temporary dev-only page (`frontend/__audit_citations.html` and
  `src/__audit_citations.tsx`, deleted afterwards and never imported by the app) rendered the real
  `EvidenceList` with synthetic records:
  - Verified sources link to exactly `https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=34ebeea1-6812-4697-84c4-b2ae4f39e55f`,
    with `target=_blank`, `rel="noopener noreferrer"`, accessible name "Open source 1 (opens in new tab)",
    and keyboard-tabbable.
  - "Supports a verified claim" appears only on the supporting record.
  - The off-allowlist host, the `javascript:` URL, the unverified record and the rejected placeholder have
    no link.
  - Clicking fired a new-tab open to `dailymed.nlm.nih.gov`; the pane blocks tabs opened by automation.
    Navigating to the exact `href` showed "DailyMed - LISINOPRIL tablet", BluePoint Laboratories, containing
    the set ID and, verbatim, "Potassium-sparing diuretics (spironolactone, amiloride, triamterene, and
    others) can increase the risk of hyperkalemia".
  - **No verified link exists in a real production result**, because the live corpus has no verified source.

## 4. Original issues

| Issue | State |
|---|---|
| NVIDIA vision timeout | **Reproduced live**, and shown to be an NVIDIA-side outage window: the 11b and 90b models both stalled at the same time, after 9/10 successes earlier. Mitigated (bounded attempts, classified error, correct UI). **Not fixed**: with NVIDIA down, extraction fails. Groq qwen works (decision 1). |
| Confirmation shown green after a failed extraction | **Fixed**, browser-verified on a real failure |
| Manual-mode "Not run" | **Fixed** ("Not applicable") |
| "Verified" medication badge | **Fixed** ("Identity resolved" plus method) |
| Trust score 0.00 | **Fixed** ("Not computed") |
| Placeholder / shared sources | **Fail closed**, no links |
| NVIDIA LLM 404 | Not avoided in every case. Groq is first in automatic mode, so NVIDIA is reached only after a Groq failure. Selecting NVIDIA by hand always fails (the model list still marks it available). |
| 127.0.0.1:5173 unreachable via `start_servers.cmd` | **Found and fixed** this pass |
| Evidence-backed lisinopril + spironolactone answer | **Blocked**: REL-LIVE-0003 needs a severity grade and researcher approval |

## 5. Tests (current tree)

| Check | Kind | Result |
|---|---|---|
| Backend `pytest` with `TESTING=1` | NLI keyword stand-in, fake or simulated providers | PASSED 1565, exit 0 |
| `test_live_evidence_provenance.py` without `TESTING` | real PubMedBERT NLI | PASSED 17 (earlier this day; unchanged since) |
| Frontend `vitest`, `tsc -b` | jsdom | PASSED 123 / 19 files; tsc exit 0 |
| Frontend lint | static | 0 errors, 3 warnings (the baseline count) |
| Browser scenarios 1–3, citation fixture | real browser, real backend, real NVIDIA/RxNav | PASSED as described in 3 |
| REL-LIVE-0003 and corpus integrity | hashes | PASSED (manifest hashes, chunk hash, verbatim span, capture SHA; corpora identical to `baf6c93`) |
| Linux checkout | — | NOT RUN |

## 6. Remaining items

1. **Vision availability:** NVIDIA vision stalls account-wide at times. Decision needed on Groq
   `qwen/qwen3.8-27b` as a second vision provider (it needs a small code change: the current fallback is
   same-provider only).
2. **Commit `a96e171` lacks the audit folder** that its tests read (see 1).
3. First request after startup: about 20 s of model loading with no progress message.
4. `.env`/`.env.local` disagree on `LLM_PROVIDER` and `GROQ_MODEL`. `.env.local` wins (Groq,
   gpt-oss-120b). Not changed; your files.
5. Audit findings still open: pending analyses kept in memory, provider error text reaching the UI,
   `/ingest` fake success, the model list marking NVIDIA available.
6. Clinical evidence: no verified source in the live corpus; REL-LIVE-0003 pending and ungraded.

## 7. Addendum: Groq vision fallback (decided by the user, 2026-10-22)

The user chose "Add Groq fallback". NVIDIA stays primary. After its attempts fail on availability
(timeout, network, 5xx, model not found), Groq `qwen/qwen3.8-27b` is tried once, inside the same 75 s
deadline. Authentication, rate-limit and bad-request failures do not move to Groq.

Changes (uncommitted):
- `openai_vision_backend.py`: a `fallback_backend` target after NVIDIA's models; attempts record the
  provider. The dead `last_model_used` is removed.
- `vision_interfaces.py`: `provider_used` on the result.
- `live_application.py`: SSE `vision_provider` names the provider that answered.
- `app.py`: wired when `GROQ_API_KEY` is set. `GROQ_VISION_MODEL` overrides the model; `GROQ_VISION_MODEL=`
  (empty) disables it. Startup log: `fallback_provider=groq_vision/qwen/qwen3.8-27b`.
- Tests: 6 new in `tests/providers/test_vision_fallback_and_timeouts.py`.

Data note: when NVIDIA fails, the uploaded prescription image is also sent to Groq.

Results:
- Backend suite 1571 passed (`TESTING=1`); ruff clean; Bandit exit 0; gitleaks on the diff: no leaks.
- Live: Groq qwen through the app's own adapter read both drugs correctly in 1.7 s (during the NVIDIA outage).
- Browser image run after the restart: NVIDIA had recovered and answered in 8.0 s on 1 attempt (`nvcf-reqid`
  logged), so the fallback was not needed. Confirmation, then the identity-gate abstention, 7 of 11 steps.
  **A browser run in which Groq serves was not observed**, because NVIDIA was up by then.
