# Adaptive Trust-Aware Medical RAG

**Research testbed for evidence-grounded pharmacology question answering — not a clinical decision system.**

> **Non-clinical disclaimer.** This software is a research prototype. It is not an FDA-approved or otherwise certified medical device and must not be used for diagnosis, prescribing or any patient care. Every output is a research artifact that may be wrong or incomplete, and the system is designed to abstain rather than guess.

Status as of commit `9bae325` (2026-10-18): the live application runs end to end with real providers and real embeddings and abstains safely on the synthetic test cases. It does **not** yet release evidence-backed answers, because no drug-relationship record has been approved by the researcher. See [Project status](#project-status).

---

## Research question

Does adaptive trust-aware retrieval — with entity attribution, source validation, contradiction detection, prompt-injection defense, retrieval-poisoning defense, claim-level verification and controlled abstention — reduce hallucinated or misattributed pharmacological evidence compared with conventional semantic-similarity medical RAG?

The domain is evidence-based pharmacology, in particular adverse drug interactions. Abstention is a correct and expected outcome when evidence is missing, below the trust threshold for the question's risk tier, or contradictory.

---

## What the application does today

The live application (`POST /api/v1/analyze*`, streamed over Server-Sent Events) runs this pipeline for each request. Details, modules and event schemas are in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

1. **Input** — drug names typed by the user, or a prescription image (JPEG/PNG/WebP, at most 5 MB). Optional patient context and optional *Additional Instructions*, both screened as untrusted data; an instruction aimed at the system is rejected (`INPUT_REJECTED`).
2. **Image extraction and confirmation** — a vision model reads candidate medication names; the reply must be a single JSON object in the expected schema or the request fails closed. The user confirms the medications before anything is analysed.
3. **Drug identity** — names are resolved to RxNorm concepts (RxCUI) from a local cache or the RxNav API.
4. **Retrieval** — hybrid BM25 + dense (all-MiniLM-L6-v2) retrieval over the frozen live corpus; each chunk's SHA-256 is checked against its provenance record and poisoned or altered chunks are blocked.
5. **Risk tier and eligibility** — a multi-drug question is R2 (threshold 0.60); R3 (0.75) only from an approved relationship record. Chunks that name none of the requested drugs are excluded before scoring.
6. **Generation** — an LLM writes a structured answer from the eligible evidence only. The provider that actually answered is recorded (`served_by`).
7. **Claim and citation verification** — every factual statement is checked against the cited evidence (PubMedBERT NLI plus canonical relationship identity). A pairwise drug claim needs an approved relationship record on the cited chunk.
8. **Safety gate** — an answer is released only if every statement is verified; otherwise the system abstains and shows why, with the evidence it checked. Evidence URLs are shown as links only when verified for that chunk.

### Implementation status

| Component | Status |
|---|---|
| Live pipeline: names → RxNorm → retrieval → trust → generation → verification → abstention | **Implemented and tested** (unit, e2e and real-provider browser runs) |
| Prescription-image extraction (NVIDIA vision) with strict JSON schema validation | **Implemented and tested** (browser run on the committed build, synthetic image) |
| Medication confirmation contract (objects only) | **Implemented and tested** |
| Risk tier R2 default, R3 only from an approved record; unrelated-evidence exclusion | **Implemented and tested** |
| Provider/model trace (`served_by`) for answers, abstentions and errors | **Implemented and tested** (released-answer path in tests only) |
| Verified-only evidence links | **Implemented and tested**; no source is verified yet, so all corpus links show as text |
| Versioned relationship records (V1, V2 with own evidence file) | **Implemented and tested**; **no record approved** (REL-LIVE-0001 and REL-LIVE-0002 pending) |
| Evidence-backed (released) answers on live data | **Pending researcher approval** of a relationship record |
| Research harness, ablation variants A–F, CLI evaluation | Implemented; published A–F numbers are **simulation** results (see below) |
| Human relevance annotation, claim-evidence benchmark, Free Replication V1, Cognee comparison | **Blocked** on human labels or researcher decisions ([register](reports/audit/blocked_issue_register.md)) |

---

## Evidence sources

| Source | Status |
|---|---|
| `data/live_medical/LIVE_MEDICAL_CORPUS_V2.json` — 14 frozen chunks (11 DailyMed, 2 PubMed, 1 openFDA) with SHA-256 provenance and MiniLM embeddings | In use. Frozen: never edited. None of its URLs is verified (11 placeholder DailyMed set IDs, 1 PubMed ID shared by two documents, 1 generic openFDA URL) |
| RxNav (RxNorm) API + local entity cache | In use for drug identity |
| Relationship records `data/live_medical/relationships/` (V1) | Loaded only when the manifest is APPROVED by a named person with matching hashes; REL-LIVE-0001 is a pending candidate |
| V2 relationship evidence (e.g. byte-exact DailyMed label text) | Loader implemented (`bf29fe8`); candidate REL-LIVE-0002 prepared and reviewed but **not approved** and not placed in `data/` |

---

## Providers

Configured from environment variables (names only; see [docs/CONFIGURATION.md](docs/CONFIGURATION.md)):

| Role | Provider / model (default) |
|---|---|
| Answer generation | NVIDIA `nvidia/nemotron-3-super-120b-a12b`, Groq `openai/gpt-oss-120b`, Cloudflare Workers AI `@cf/meta/llama-3.3-70b-instruct-fp8-fast` (4096-token limit); `mock-llm` for tests |
| Prescription vision | NVIDIA `meta/llama-3.2-11b-vision-instruct` |
| Embeddings | `all-MiniLM-L6-v2` (local, sentence-transformers) |
| Claim verification (NLI) | `pritamdeka/PubMedBERT-MNLI-MedNLI` (pinned revision) |

In automatic mode the configured providers are tried in order NVIDIA, Groq, Cloudflare (`LLM_PROVIDER` moves one to the front) with failover; a model chosen manually in *Advanced settings* is used without failover. The live app registers only these three; Hugging Face, Gemini and FreeLLMAPI adapters exist for the research harness but are not wired into the live router.

---

## Quick start (local)

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), Node.js with npm. Full details and troubleshooting: [docs/CONFIGURATION.md](docs/CONFIGURATION.md).

```bash
# Backend dependencies (never pip install globally)
uv sync

# Configure: copy the template and fill in your own keys locally; never commit .env
cp .env.example .env

# Backend (FastAPI) on http://127.0.0.1:8000
uv run python -m uvicorn --app-dir src adaptive_trust_medical_rag.api.app:app --host 127.0.0.1 --port 8000

# Frontend (Vite + React) on http://localhost:5173, proxying /api to port 8000
cd frontend && npm install && npm run dev
```

Do not set `TESTING=1` for a real run: it replaces the embedding model with a stub.

---

## Tests and validation

The commands, what each suite covers and the latest verified results are in [docs/TESTING.md](docs/TESTING.md). Latest exact-build result (commit `9bae325`, fresh worktree): **1470 passed, 4 skipped, 0 failed** backend; ruff, Bandit, gitleaks, integrity scripts and the frozen-hash line-ending audit clean.

```bash
TESTING=1 uv run pytest -q          # backend (TESTING=1 is correct for tests only)
cd frontend && npm test && npm run build && npm run lint
```

---

## Research harness and ablation variants (A–F)

The `medical-rag` CLI (`query`, `ingest`, `eval`, `report`, `db`, `health`, `research-run`) runs the research harness across six variants: A vanilla LLM, B dense RAG, C hybrid RAG, D entity-attributed RAG, E trust-scored RAG, F full architecture with dual gates. See [docs/EVALUATION_PROTOCOL.md](docs/EVALUATION_PROTOCOL.md).

> **Results caveat.** The A–F metric tables in `reports/results/` and earlier versions of this README come from a **simulation profile** (`MockVariantPipeline`), not from live model runs or human-labelled data. They are not evidence for the research question. The human relevance labels and claim-evidence benchmark needed for a real evaluation are still blocked (see the register).

---

## Known limitations

- No relationship record is approved, so every live analysis of an interaction pair abstains after generation; evidence-backed answers are unverified.
- NVIDIA's answer model often times out in automatic mode (30 s adapter timeout); Groq then answers after failover. Selected directly, NVIDIA has answered.
- Model-written disclaimer sentences are sometimes kept as claims and then withheld.
- The live corpus is 14 synthetic-scope chunks with unverified source URLs; it is a test corpus, not clinical coverage.
- Image extraction has been validated on one synthetic prescription image only.
- Software tests and safe abstention do not demonstrate clinical effectiveness.

---

## Project status

The authoritative status of every open item is [reports/audit/blocked_issue_register.md](reports/audit/blocked_issue_register.md). Validation runs and reports are under [reports/live_validation/](reports/live_validation/). The application freeze, the evidence-backed-answer milestone and any release are separate researcher decisions; none is declared here.

## Documentation map

| Document | Purpose |
|---|---|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Live pipeline data flow, modules, endpoints, SSE events; research-harness architecture |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | Setup, environment variables, providers, ports, troubleshooting |
| [docs/TESTING.md](docs/TESTING.md) | Test suites, security and integrity checks, browser scenarios, latest results |
| [docs/EVALUATION_PROTOCOL.md](docs/EVALUATION_PROTOCOL.md) | Research evaluation protocol |
| [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) | Threat model |
| [reports/audit/blocked_issue_register.md](reports/audit/blocked_issue_register.md) | Current blockers and decisions |
| [AGENTS.md](AGENTS.md) | Operating rules for contributors and agents |

## License

MIT, as declared in `pyproject.toml` (no separate LICENSE file is included).
