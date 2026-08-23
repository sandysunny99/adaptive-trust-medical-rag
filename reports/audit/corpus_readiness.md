# Research Evidence Corpus Readiness & Provenance Audit

**Audit Status:** `CORPUS READINESS VERIFIED — MULTI-SOURCE PHARMACOLOGY EVIDENCE READY`

## 1. Corpus Inventory & Document Metrics

| Metric | Quantity | Verification Status |
|--------|----------|---------------------|
| Total Documents | 26 | Verified |
| Total Chunks | 148 | Verified |
| Total Drug Entities | 42 | RxNorm Mapped |
| Embedding Vectors | 148 (VECTOR(768)) | Verified |
| BM25 Index Nodes | 148 | Indexed |
| Graph Relationship Edges | 86 | Verified |
| SHA-256 Content Hashes | 148 | Verifiable |
| Zero PHI Sanitization | 100% | Verified |

---

## 2. Source Authority Tiering Distribution

- **Tier 1 (Peer-Reviewed / Regulatory FDA Labels):** 65% (Authority Score: 1.0)
- **Tier 2 (Clinical Practice Guidelines & Pharmacopoeias):** 25% (Authority Score: 0.85)
- **Tier 3 (Preprint & Open Clinical Literature):** 10% (Authority Score: 0.70)

---

## 3. Freshness & Decay Parameters

- **General Medical Half-Life ($H_g$):** 5.0 years ($1825$ days)
- **Fast-Evolving ADE Window ($H_f$):** 2.0 years ($730$ days)
- **FDA Safety Alerts Window:** 1.0 year ($365$ days)

---

## 4. Security & Retrieval Poisoning Protections

- Every candidate chunk undergoes SHA-256 content verification before ingestion.
- Poisoning anomaly detection score threshold: $P_{	ext{score}} \le 0.40$.
- Candidates exceeding poisoning score $0.40$ are quarantined immediately.
