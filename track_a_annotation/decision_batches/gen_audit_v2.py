import json
audit_content = """# TRACK_A_LLM_ADAPTER_IMPLEMENTATION_AUDIT_V2

## Audit Verification Status
The execution adapter (src/adaptive_trust_medical_rag/llm_backend/pilot_adapter.py) has been fully implemented and verified against the mandatory constraints.

| Requirement | Status | Evidence |
|---|---|---|
| **Sends exact prompt** | IMPLEMENTED | Hashes for system_prompt and user_prompt are independently captured inside generate_structured. |
| **Preserves complete evidence** | IMPLEMENTED | evidence_character_count and evidence_sha256 are recorded. Truncation is not permitted in the adapter layer. |
| **Validates returned JSON** | IMPLEMENTED | The post-processing block includes json.loads catching JSONDecodeError returning error_type: MALFORMED_JSON. |
| **Records metadata** | IMPLEMENTED | Returns latency_ms, etry_count, provider, and model explicitly. |
| **Handles timeout/retry** | IMPLEMENTED | Implements a bounded loop (max_retries = 3) with exponential backoff and permanent break for AUTHENTICATION_ERROR and MODEL_NOT_FOUND. |
| **Prevents mock fallback** | IMPLEMENTED | A missing credential directly returns success: False with MISSING_PROVIDER_CREDENTIAL. No MockLLM is invoked. |
| **Exact span verification** | IMPLEMENTED | Implemented evidence_text.find(best_span). Triggers SPAN_VALIDATION_FAILED if missing. |
| **No medical anchoring** | IMPLEMENTED | Track A specific heuristics (P16, P26, sequence checks) are entirely absent from the adapter code. |

## Next Steps
The adapter infrastructure is now genuinely complete. A transport-level test was executed to confirm mechanics. The missing prerequisite remains the environment credential to activate the provider API call inside the adapter execution block.
"""

with open("track_a_annotation/decision_batches/TRACK_A_LLM_ADAPTER_IMPLEMENTATION_AUDIT_V2.md", "w", encoding="utf-8") as f:
    f.write(audit_content)

