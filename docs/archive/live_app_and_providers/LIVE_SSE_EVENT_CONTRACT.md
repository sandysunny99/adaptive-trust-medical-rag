# Live SSE Event Contract

The Server-Sent Events (SSE) stream emits the following events for the live application pipeline:

1. **stage_update**
   - Payload: `{"stage": string, "status": "running" | "complete", "message": string, "timestamp": string}`
   - Stages: `uploading`, `extracting`, `normalizing`, `retrieving`, `trust_evaluating`, `security_checking`, `generating`, `claim_verifying`, `safety_gating`.

2. **rxnorm**
   - Payload: `{"entities": list[MedicationInfo]}`

3. **retrieval**
   - Payload: `{"evidence_count": int, "sources": list[string]}`

4. **security**
   - Payload: `{"injection_status": string, "poisoning_status": string, "poisoning_reason": string | null}`

5. **trust**
   - Payload: `{"overall_score": float, "threshold": float, "risk_class": string, "is_eligible": boolean, "factors": dict, "missing_factors": list}`

6. **abstention**
   - Payload: `{"reason": string, "trust": dict}`

7. **result**
   - Payload: Final structured RAG verification object (including all medication claims, warnings, interactions, verifications).

8. **error**
   - Payload: `{"code": string, "message": string}`
   - Common Codes: `PROVIDER_CONFIGURATION_REQUIRED`, `PROVIDER_FAILURE`, `LLM_OUTPUT_VALIDATION_FAILURE`, `LLM_ERROR`.
