# Live Application Prompt Specification

## 1. Description
The `LIVE_APP_PROMPT_V1.txt` is an isolated prompt specifically used for the actual web service (separately tracked from `REAL_LLM_PROMPT_V1` which is bound to the frozen research harness).

## 2. Structured Output Schema
The prompt explicitly mandates that the LLM return a structured JSON conforming strictly to:
- `conclusion`
- `interactions` (array of objects outlining drugs involved, interaction details, evidence status, and sources)
- `adverse_reactions` (array of reactions with severity, frequency, and evidence level)
- `warnings` (array of string warnings)
- `food_guidance` (array of administration details and timing)
- `patient_considerations` (array of explicitly provided context factors and relevant considerations)
- `claims_for_verification` (array of factual claims that trigger the `ClaimVerifierV2`)

## 3. Evidence Grounding Enforcement
The prompt stringently includes instructions NOT to fabricate information ("Do NOT hallucinate"), NOT to infer conditions, and to explicitly state uncertainty where insufficient evidence is provided.

## 4. Hash Fingerprint
- **Version:** `LIVE_APP_PROMPT_V1`
- **Hash:** `e4a63bd364718237896bc4b2667614739172564b6eaafff2fca950ccf268460c`
- **Integrity Validation File:** `LIVE_APPLICATION_PROMPT_HASH.json`
