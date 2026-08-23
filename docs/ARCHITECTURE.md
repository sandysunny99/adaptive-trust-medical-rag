# Adaptive Trust-Aware Medical RAG: Architecture & Technical Specification

## 1. System Architecture Overview

The Adaptive Trust-Aware Medical RAG platform implements a dual-safety-gated pipeline specifically designed for high-risk medical and pharmacological queries.

```
+-----------------------------------------------------------------------+
|                           User Query Input                            |
+-----------------------------------┬-----------------------------------+
                                    │
                       [Input Sanitizer & Classifier]
                                    │
                                    ▼
+-----------------------------------------------------------------------+
|                    Evidence Eligibility Gate (Pre-Gen)                 |
|  - Source Authority Tiering (Peer-Reviewed > FDA > Preprint)          |
|  - Freshness Exponential Decay: exp(-ln(2) * age / half_life)          |
|  - Entity Match Verification (RxNorm RxCUI / scispaCy)                |
|  - Multi-Factor Trust Score Calculation                               |
|  - Risk Class Threshold Gating (R0: 0.30, R1: 0.45, R2: 0.60, R3: 0.75) |
+-----------------------------------┬-----------------------------------+
                                    │
                 ┌──────────────────┴──────────────────┐
                 │                                     │
           (Passed Gate)                        (Failed Gate / Contradiction)
                 │                                     │
                 ▼                                     ▼
+---------------------------------+   +---------------------------------+
|        Hybrid Retrieval         |   |      Controlled Abstention      |
|  - BM25 Keyword Search          |   |  - Standard Structured Template |
|  - Dense Vector (pgvector)      |   |  - Missing Evidence Explanation |
|  - Graph Candidate Expansion    |   |  - Audit Log Event Recorded     |
|  - Reciprocal Rank Fusion (RRF) |   +---------------------------------+
+----------------┬----------------+
                 │
                 ▼
+---------------------------------+
|    Context-Grounded LLM Gen     |
|  - Strictly Grounded Prompts    |
|  - Citation Id Linking          |
+----------------┬----------------+
                 │
                 ▼
+-----------------------------------------------------------------------+
|                    Answer Safety Gate (Post-Gen)                       |
|  - Claim Extraction & Verification                                    |
|  - Citation Verification                                              |
|  - Hallucinated PMIDs/Urls Elimination                                 |
|  - NLI Contradiction Filtering                                        |
+-----------------------------------┬-----------------------------------+
                                    │
                                    ▼
+-----------------------------------------------------------------------+
|                      Final Verified RAG Output                        |
+-----------------------------------------------------------------------+
```

---

## 2. Dual Safety Gate Specification

### 2.1 Evidence Eligibility Gate (Pre-Generation)

Before feeding retrieved context into LLM prompt construction, each candidate chunk must satisfy minimum evidence eligibility criteria:

1. **Source Authority Score ($S_{\text{auth}}$):**
   - **Tier 1 (Peer-Reviewed / Clinical Guidelines):** $1.00$
   - **Tier 2 (FDA Labels / Package Inserts):** $0.90$
   - **Tier 3 (Preprints / Unreviewed Literature):** $0.50$
   - **Tier 4 (Unvalidated External / Unknown):** $0.10$

2. **Freshness Score ($S_{\text{fresh}}$):**
   - $S_{\text{fresh}} = \exp\left(-\frac{\ln(2) \cdot \text{age\_years}}{\text{half\_life}}\right)$
   - Default half-life: 5.0 years for clinical evidence.

3. **Entity Match Score ($S_{\text{ent}}$):**
   - Normalized scispaCy NER / RxNorm RxCUI exact match: $1.00$
   - Generic to brand alias match: $0.85$
   - Related drug class match: $0.50$
   - Unmatched: $0.00$

4. **Multi-Factor Trust Score Calculation:**
   $$T_{\text{doc}} = w_{\text{auth}} S_{\text{auth}} + w_{\text{fresh}} S_{\text{fresh}} + w_{\text{ent}} S_{\text{ent}} + w_{\text{rep}} S_{\text{rep}}$$
   Default weights: $w_{\text{auth}} = 0.35$, $w_{\text{fresh}} = 0.20$, $w_{\text{ent}} = 0.30$, $w_{\text{rep}} = 0.15$.

5. **Risk Tier Abstention Thresholds:**
   - **R0 (General OTC / Lifestyle):** $T \ge 0.30$
   - **R1 (Indications / Dosing):** $T \ge 0.45$
   - **R2 (Severe Drug-Drug Interactions):** $T \ge 0.60$
   - **R3 (Lethal Contraindications / ADEs):** $T \ge 0.75$

### 2.2 Answer Safety Gate (Post-Generation)

Following response generation:

1. Claim extraction divides the generated text into individual verifiable factual assertions.
2. Each claim is cross-referenced against the retrieved evidence chunks.
3. If a claim lacks supporting evidence chunks or contradicts authoritative sources, it is removed or the response triggers controlled abstention.
4. Nonexistent PMIDs, URLs, or fabricated publication dates are stripped deterministically.

---

## 3. Database Entity-Relationship Schema

The database relies on PostgreSQL with the `pgvector` extension:

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────────┐
│ evidence_sources │──────<│    documents     │──────<│   evidence_chunks    │
│ (authority, tier)│       │ (sha256, status) │       │ (embedding vector)   │
└──────────────────┘       └──────────────────┘       └──────────────────────┘
                                                                 │
                                                                 │
                           ┌──────────────────┐       ┌──────────┴───────────┐
                           │   audit_events   │       │  evidence_provenance │
                           │ (query_hash, PK) │       │ (SHA256 hash log)    │
                           └──────────────────┘       └──────────────────────┘
```

- **`evidence_sources`**: Stores root publisher authority scores, reputation metrics, and verification status.
- **`documents`**: Ingested medical documents with SHA-256 content hashes, publication dates, and source IDs.
- **`evidence_chunks`**: Chunked text snippets with 768-dimensional embeddings (`VECTOR(768)`) and IVFFlat vector index.
- **`evidence_provenance`**: Audit log recording ingestion timestamps, chunk hashes, and validation history.
- **`audit_events`**: Telemetry log storing SHA-256 query hashes (`query_hash`), risk tier, gate decision, and trust scores. Zero raw PHI is stored.

---

## 4. Threat Model & Security Mitigations

| Threat | Attack Vector | System Mitigation |
|--------|---------------|-------------------|
| **Prompt Injection** | User query includes override directives (`Ignore previous instructions`) | Regex & semantic input sanitizer strips markers before prompt generation |
| **Retrieval Poisoning** | Malicious evidence inserted into vector index | SHA-256 ingestion validation, source authority tiering, quarantine checks |
| **PHI Leakage** | User query contains SSN / Patient Identifiers | Deterministic PHI scrubber; audit log records SHA-256 hash only (`query_hash`) |
| **Hallucinated Citations** | Model fabricates non-existent PMIDs / URLs | Answer Safety Gate validates all PMIDs against retrieved session context |
| **Test Set Leakage** | Frozen evaluation cases used for tuning/indexing | Programmatic guard (`allow_test=True`) blocking test split access in pipeline |

---

## 5. Research Integrity Policy

- **Frozen Test Set:** The 500+ case test set is frozen and never used for prompt engineering, threshold tuning, or indexing.
- **Bootstrap Confidence Intervals:** All evaluation reports log 95% bootstrap CIs ($N=1000$ resamples) alongside point estimates.
- **Deterministic Logging:** Full experiment config hashes (`model`, `prompt_version`, `trust_weights`, `retriever_config`) are recorded for exact scientific reproducibility.
