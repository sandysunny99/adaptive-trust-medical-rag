# HUMAN ACTION QUEUE

**Date:** 2026-10-03  
**Stage:** CONTROLLED SCIENTIFIC VALIDATION

This queue lists the immediate human actions required to unblock execution phases.

## 1. DECISION_TRACK_A_002: Review Batch 004
- **Action:** Review the four annotated positions in `TRACK_A_BATCH_004_HUMAN_DECISION_PACKET.md`. Confirm the labels, grades, rationales, and exact evidence spans.
- **Why Required:** The LLM serves only as decision support. Ground truth relevance annotations require explicit human confirmation.
- **Evidence Provided:** Query, Retrieved Evidence, LLM Advisory Analysis.
- **Researcher Decision:** Provide final label/span confirmation.

## 2. DECISION_GATE_C_001: Select first Gate C provider/model
- **Action:** Review `GATE_C_PROVIDER_SELECTION_DECISION_PACKET_V2.md` and select the primary live validation provider (Groq, Cloudflare, Hugging Face, FreeLLMAPI).
- **Why Required:** Provider selection alters the experimental execution path. Gemini is restricted to Phase 15.
- **Evidence Provided:** Provider capabilities, credential requirements, LLM continuity analysis.
- **Researcher Decision:** Confirm provider choice (e.g., Groq).

## 3. CREDENTIAL_ACTION: Provide credential
- **Action:** Inject the API key corresponding to the selected provider from Action 2 (e.g., `GROQ_API_KEY`) into the environment.
- **Why Required:** Required to execute Gate C Preflight and Live Validation.
- **Evidence Provided:** N/A
- **Researcher Decision:** Safely configure the environment without exposing the secret.
