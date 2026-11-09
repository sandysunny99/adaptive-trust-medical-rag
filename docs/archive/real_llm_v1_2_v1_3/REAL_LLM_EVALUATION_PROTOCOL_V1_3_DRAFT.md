# REAL_LLM_EVALUATION_PROTOCOL_V1_3_DRAFT

## 1. Provider Selection & Readiness
- Continue with `openai/gpt-oss-120b` or select a stable provider with guaranteed TPM limits suitable for the prompt size.

## 2. Rate-Limit Constraints & Pacing
- Implement explicit delays between requests (e.g., 5 seconds).

## 3. Permitted Retry Behavior
- Retry up to 3 times on HTTP 429. Exponential backoff starting at 5 seconds.

## 4. Stopping Criteria
- If 10 consecutive provider failures occur, abort the run.

## 5. Minimum Successful-Generation Requirement
- Both arms must achieve comparable generation opportunity.

## 6. Frozen Artifacts
- Prompt, dataset, and retrieval must remain strictly identical to V1.2.
