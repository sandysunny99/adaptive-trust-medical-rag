# API Failure, Timeout, & Fallback Policy

**Specification Version:** `1.0.0`  
**Project:** Adaptive Trust-Aware Medical RAG  

---

## 1. Overview

External API providers may experience network latencies, rate limits (HTTP 429), server errors (HTTP 5xx), or temporary outages. This policy defines the deterministic failure handling, retry backoff, health check diagnostics, and frozen snapshot fallback rules enforced across all evidence adapters.

---

## 2. Timeout & Rate Limit Controls

| Provider | Base Endpoint | HTTP Timeout | Rate Limit (W/o Key) | Rate Limit (W/ Key) | Max Retries | Retry Backoff |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **NCBI PubMed** | `https://eutils.ncbi.nlm.nih.gov/` | 5.0s | 3 req/sec | 10 req/sec | 3 | Exponential (0.5s, 1.0s, 2.0s) |
| **Europe PMC** | `https://www.ebi.ac.uk/europepmc/` | 5.0s | 10 req/sec | N/A | 3 | Exponential (0.5s, 1.0s, 2.0s) |
| **NLM RxNorm** | `https://rxnav.nlm.nih.gov/` | 4.0s | 20 req/sec | N/A | 2 | Exponential (0.3s, 0.6s) |
| **openFDA** | `https://api.fda.gov/` | 5.0s | 4 req/sec | 240 req/min | 3 | Exponential (0.5s, 1.0s, 2.0s) |

---

## 3. Fallback Modes by Execution Context

1. **Live Application Mode:**
   - On provider timeout or HTTP 5xx: Execute up to `max_retries` with exponential jitter backoff.
   - If retries fail: Fall back to local verified snapshot corpus if available, or return structured `API_FAILURE` record. Never fabricate response data.
2. **Research Evaluation Mode:**
   - Record explicit `API_FAILURE` status in evaluation telemetry.
   - Do NOT substitute synthetic dummy text.
3. **Frozen Benchmark Mode:**
   - Use strictly local pre-recorded JSON snapshots in `experiments/manifests/external_sources_v1.json`. Zero network calls permitted.

---

## 4. Health Check Specification

Every adapter implements `.health_check() -> bool`:
- Sends lightweight ping query (e.g. `einfo.fcgi` for PubMed).
- Returns `True` if status code == 200 and latency < 3000ms.
- Returns `False` if endpoint is unreachable or timing out. System degradation is logged silently without crashing the application.
