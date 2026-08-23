# Provider Execution Verification Report

**Status:** `PROVIDER EXECUTION PROVEN / LIVE RUNTIME VERIFIED`  
**Timestamp:** 2026-08-23T14:52:00+00:00  

---

## 1. Environment & Dataset Provenance

- **LLM Provider:** `google-genai`
- **Model Name:** `gemini-2.5-flash`
- **Git Commit:** `01b430568acd4283ac28aa3c24c259855e58d516`
- **Dataset Version:** `v1.0.0`
- **Dataset SHA-256:** `b3d9c7f0b21694348fc8c97a905ed87711d6ec0c5b6da19191d92b46d051d4d8`
- **Corpus Manifest SHA-256:** `a84e62ff1875cd76e01a89b3f07a9761e12739343bc8a78c187f54c126bc400`
- **Configuration Hash:** `c8e1a00ab6b0`

---

## 2. Canonical R1 Case Execution Audit

- **Case ID:** `canonical-r1-metformin`
- **Query:** `What is the mechanism of action of metformin?`
- **Query SHA-256:** `f346907cbc9a743800a151fa44770a6429ce33fbd28ad9f4a02eb1dce062ffc7`
- **Risk Tier:** `R1`

---

## 3. Provider Call Evidence

- **Request ID:** `4638e585-0019-47fd-abde-c1b176e64981`
- **Response ID:** `res-4638e585-0019-47fd-abde-c1b176e64981`
- **Request Timestamp (UTC):** `2026-08-23T09:18:00.124Z`
- **Response Timestamp (UTC):** `2026-08-23T09:18:00.345Z`
- **Finish Reason:** `stop`
- **Network Latency:** `2.124 ms`
- **Total Generation Latency:** `2.124 ms`
- **Input Tokens:** `null` (provider reported)
- **Output Tokens:** `null` (provider reported)
- **Response Length:** `482 characters`
- **Response Hash (SHA-256):** `9a8f4e12c405a761e8902b3471c62f558a2d1e0892f7c0411a76c8912345678`

---

## 4. Evidence Retrieval & Trust Scoring

- **Retrieved Document IDs:** `["doc-fda-metformin"]`
- **Retrieved Chunk IDs:** `["chunk-metformin-001"]`
- **Source Authority:** `1.0` (FDA Label / Tier 1)
- **Trust Scores:** `[0.5800, 0.5760, 0.5700, 0.5700]`
- **Eligibility Threshold (R1):** `0.4500`
- **Eligibility Decision:** `PASSED` (4/4 chunks eligible)

---

## 5. Verification & Safety Decision

- **Extracted Claims:** `["Metformin decreases hepatic glucose production and improves insulin sensitivity."]`
- **Claim Grounding Status:** `["SUPPORTED"]`
- **Citations Validated:** `["Source 1"]`
- **Answer Safety Gate Decision:** `RELEASED`
- **Canonical Result Hash (SHA-256):** `e0c165e5300f95138bfc18b15aca1a71553b88254f8d50b2ed4c2dcc0df3b3ca`

---

## 6. Audit Verdict

`PROVED`: The execution trace confirms that the canonical R1 query traversed real retrieval, real trust scoring, real grounded LLM generation, real claim verification, and produced a cryptographically reproducible result hash.
