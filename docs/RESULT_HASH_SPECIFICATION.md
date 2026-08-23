# Deterministic Result Hash Specification

**Specification Version:** `1.0.0`  
**Project:** Adaptive Trust-Aware Medical RAG  
**Standard:** Cryptographic Case-Level Evidence Traceability  

---

## 1. Overview

The **Canonical Result Hash** (`result_hash`) provides an immutable, cryptographically reproducible SHA-256 digest of every case-level evaluation result. It ensures that evaluation records cannot be retroactively tampered with, edited, or fabricated without invalidating the evidence hash.

---

## 2. Included Payload Fields

The `result_hash` is computed exclusively from the following 7 deterministic fields:

| Field Name | Type | Description / Formatting Rules |
| :--- | :--- | :--- |
| `case_id` | `str` | Unique evaluation case identifier. |
| `variant` | `str` | Ablation variant identifier (`A`, `B`, `C`, `D`, `E`, `F`). |
| `query_hash` | `str` | SHA-256 hex digest of the raw user query (64 chars, lowercase hex). |
| `generated_answer_hash` | `str` | SHA-256 hex digest of the generated LLM answer (64 chars, lowercase hex). |
| `retrieval_ids` | `list[str]` | Sorted list of retrieved document/chunk identifiers (`sorted(doc_ids)`). |
| `trust_values` | `list[float]` | List of trust scores, rounded to 4 decimal places (`[round(x, 4) for x in trust_scores]`). |
| `verification_state` | `list[str]` | Sorted list of claim verification statuses (`sorted(claim_verification)`). |

---

## 3. Excluded Non-Deterministic Fields

The following fields are explicitly **EXCLUDED** from the result hash payload to preserve hash stability across re-verifications:

- Wall-clock timestamps (`request_started_at`, `response_received_at`, experiment dates)
- Latency and stage durations (`network_latency_ms`, `total_latency_ms`, `stage_timings`)
- Provider session UUIDs (`request_id`, `response_id`)
- Local filesystem paths or log paths

---

## 4. Deterministic Serialization & Hashing Algorithm

The payload dictionary MUST be serialized using compact, sorted JSON formatting before computing the SHA-256 digest:

```python
import hashlib
import json

payload = {
    "case_id": case_id,
    "variant": variant,
    "query_hash": query_hash,
    "generated_answer_hash": generated_answer_hash,
    "retrieval_ids": sorted(retrieved_documents),
    "trust_values": [round(x, 4) for x in trust_scores],
    "verification_state": sorted(claim_verification),
}

# Deterministic JSON serialization: sorted keys, no whitespace around separators
serialized_bytes = json.dumps(
    payload,
    sort_keys=True,
    separators=(",", ":"),
).encode("utf-8")

result_hash = hashlib.sha256(serialized_bytes).hexdigest()
```

---

## 5. Verification Properties

1. **Deterministic Reproducibility:** Any independent implementation following this specification will compute the exact same `result_hash` for identical input payloads regardless of dictionary insertion order.
2. **Mutation Sensitivity:** Altering any single character in `case_id`, `query_hash`, `generated_answer_hash`, `retrieved_documents`, `trust_scores`, or `claim_verification` will produce a completely different SHA-256 digest.
3. **Format Enforcement:** All valid result hashes must satisfy regex pattern `^[0-9a-f]{64}$`.
