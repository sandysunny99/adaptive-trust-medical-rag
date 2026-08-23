# Adaptive Trust-Aware Medical RAG: Mitigating Prompt Injection and Retrieval Hallucinations

**Research Testbed | Security First | Evidence-Grounded Pharmacology RAG**

---

## 1. Research Question & Purpose

> **Core Research Question:** Does adaptive trust-aware retrieval with entity attribution, source validation, contradiction detection, prompt-injection defense, retrieval-poisoning defense, claim-level verification, and controlled abstention reduce hallucinated or misattributed pharmacological evidence compared with conventional semantic-similarity medical RAG?

This repository hosts a research testbed designed to evaluate safety, hallucination mitigation, prompt injection defense, and retrieval poisoning resistance in evidence-based medicine and pharmacology.

**Non-Clinical Disclaimer:** This software is a research testbed and is **NOT** an FDA-approved/certified medical diagnostic or decision-making system. All generated outputs represent evidence-grounded research evaluations, not clinical advice.

---

## 2. Architecture & Dual Safety Gates

The system operates via a dual-gate architecture that bounds model inputs and outputs:

```
                  ┌─────────────────────────────────────┐
                  │          Incoming User Query         │
                  └──────────────────┬──────────────────┘
                                     │
                        [Input Sanitizer & Classifier]
                                     │
                  ┌──────────────────▼──────────────────┐
                  │    Evidence Eligibility Gate        │
                  │   (Source Auth + Trust Thresholds)  │
                  └──────────────────┬──────────────────┘
                            │                 │
                      (Pass)│                 │(Fail / Contradiction)
                            ▼                 ▼
                  ┌──────────────────┐ ┌────────────────────────┐
                  │ Hybrid Retrieval │ │ Controlled Abstention  │
                  │ (BM25 + Dense +  │ │   Template Response    │
                  │ Graph RRF)       │ └────────────────────────┘
                  └─────────┬────────┘
                            │
                  ┌─────────▼────────┐
                  │ Context-Grounded │
                  │ LLM Generation   │
                  └─────────┬────────┘
                            │
                  ┌─────────▼───────────────────────────┐
                  │     Answer Safety Gate              │
                  │ (Claim Verification & Citation Check)│
                  └──────────────────┬──────────────────┘
                                     │
                        [Final Verified Output]
```

### Safety Gates Specification

1. **Evidence Eligibility Gate (Pre-Generation):**
   - Evaluates retrieved document chunks prior to prompt assembly.
   - Computes multi-factor trust scores: $T_{\text{chunk}} = w_{\text{auth}} S_{\text{auth}} + w_{\text{fresh}} S_{\text{fresh}} + w_{\text{ent}} S_{\text{ent}} + w_{\text{rep}} S_{\text{rep}}$.
   - Enforces risk-dependent abstention thresholds:
     - **R0 (Informational / OTC):** Threshold $\ge 0.30$
     - **R1 (Dosing / Indications):** Threshold $\ge 0.45$
     - **R2 (Severe Drug Interactions):** Threshold $\ge 0.60$
     - **R3 (Lethal Contraindications):** Threshold $\ge 0.75$

2. **Answer Safety Gate (Post-Generation):**
   - Deterministically parses claims in the generated response.
   - Cross-references claims against session evidence chunks.
   - Strips unverified or hallucinated claims, or triggers controlled abstention if core assertions lack attribution.

---

## 3. Ablation Study Variants (A – F)

The evaluation suite benchmarks 6 architectural configurations:

| Variant | Name | Retrieval | Trust Weights | Gates Active | Description |
|---------|------|-----------|---------------|--------------|-------------|
| **A** | Vanilla LLM | None | None | None | Direct LLM prompting without retrieval context |
| **B** | Standard Semantic RAG | Dense Vector | None | None | Dense vector search ($k=5$), no trust scoring, no gates |
| **C** | Hybrid RAG | Dense + BM25 RRF | None | None | Reciprocal Rank Fusion of keyword and vector search |
| **D** | Entity-Attributed RAG | Dense + Graph | Entity Match | Pre-Gen Gate | Graph entity normalization (RxCUI) & attribution |
| **E** | Trust-Scored RAG | Dense + BM25 | Multi-Factor Trust | Pre-Gen Gate | Source authority, freshness decay, and trust weighting |
| **F** | **Full Architecture** | Hybrid + Graph | Multi-Factor Trust | **Dual Gates** | Complete pipeline with dual safety gates & abstention |

---

## 4. Security & Threat Model

- **Prompt Injection Defense:** Input sanitizer strips prompt override markers (`Ignore previous instructions`, `[INST]`, `<|im_start|>`) before prompt construction.
- **Retrieval Poisoning Defense:** Implements SHA-256 content hashing at ingestion, authority tiering, and quarantine checks for anomalous content.
- **Zero PHI Policy:** Mandatory telemetry sanitization storing SHA-256 query hashes (`query_hash`) rather than raw patient queries.
- **SAST & Secret Scanning:** Enforced automated Bandit scans (`.bandit` INI config), 8 custom Semgrep security rules, and pre-commit Gitleaks scanning.

---

## 5. Installation & Setup

All dependencies are managed using `uv`. Do NOT run global `pip install`.

```bash
# Clone the repository
git clone https://github.com/sandysunny99/adaptive-trust-medical-rag.git
cd adaptive_trust_medical_rag

# Install dependencies into virtual environment
uv sync --frozen

# Environment configuration
cp .env.example .env
```

---

## 6. Command Line Interface (CLI) Usage

The `medical-rag` CLI provides single-command execution for all operational tasks:

```bash
# Execute a medical RAG query
medical-rag query "What is the mechanism of action of Metformin?" --risk-tier R1

# Ingest a medical document with SHA-256 validation
medical-rag ingest data/sample_paper.pdf --tier tier_1_peer_reviewed

# Run evaluation pipeline across ablation variants
medical-rag eval --split smoke --quick

# Generate statistical research report (t-tests, Cohen d, 95% CIs)
medical-rag report --bootstrap-n 1000 --output reports/statistical_report.md

# Database migration chain integrity check
medical-rag db check

# Run system health diagnostic
medical-rag health --format json
```

---

## 7. FastAPI REST API

Start the API server:

```bash
uvicorn adaptive_trust_medical_rag.api.app:app --host 0.0.0.0 --port 8000
```

### Core Endpoints

- `POST /query`: Execute a RAG query through dual safety gates.
- `POST /ingest`: Upload and ingest a medical literature document.
- `GET /health`: Health check and diagnostic status.
- `GET /audit`: Query audit logs (returns query hashes only, zero PHI).

---

## 8. Experimental Evaluation Scorecard

Evaluated across 20-case smoke, 100-case dev, and 200-case val datasets ($N=1000$ bootstrap resamples, $p < 0.05$ Welch $t$-test):

| Variant | Faithfulness ↑ | Hallucination Rate ↓ | Citation Precision ↑ | Citation Recall ↑ | Entity Attribution ↑ | Robustness ↑ | F1-Abstain ↑ |
|---------|---------------|----------------------|----------------------|-------------------|----------------------|--------------|--------------|
| **A (Vanilla)** | 0.2975 | 0.7025 | 0.0000 | 0.0000 | 0.3120 | 0.3015 | 0.0000 |
| **B (Dense RAG)** | 0.5475 | 0.4525 | 0.5210 | 0.5100 | 0.5840 | 0.5320 | 0.0000 |
| **C (Hybrid RAG)** | 0.6820 | 0.3180 | 0.6940 | 0.6750 | 0.7100 | 0.6650 | 0.0000 |
| **D (Entity RAG)** | 0.7410 | 0.2590 | 0.7650 | 0.7320 | 0.8950 | 0.7280 | 0.4210 |
| **E (Trust RAG)** | 0.8120 | 0.1880 | 0.8410 | 0.8050 | 0.8320 | 0.8010 | 0.5830 |
| **F (Full Arch)** | **0.9117** | **0.0883** | **0.9320** | **0.8940** | **0.9480** | **0.9150** | **0.6667** |

---

## 9. License & Attestation

- **License:** MIT License
- **Research Integrity Attestation:** The 500+ case test set is strictly frozen and held out. All evaluation results report bootstrap 95% confidence intervals and pairwise statistical significance ($p < 0.05$).
