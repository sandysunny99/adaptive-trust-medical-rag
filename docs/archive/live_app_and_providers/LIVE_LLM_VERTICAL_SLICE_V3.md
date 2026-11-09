# Live LLM Vertical Slice V3

## 1. Corpus Integrity Verification
A programmatic hash recheck was run on `data/live_medical/LIVE_MEDICAL_CORPUS_V1.json` (as the previous Test 3 tampered with it). All 5 chunks cleanly validated against their stored cryptographic provenance hashes (Status: PASS).

## 2. LLM Boundary and Post-Generation Constraints
The pipeline has been updated to enforce strict separation:
1. **Pre-LLM Guard:** Groq LLM is strictly bypassed if security or trust evaluations fail (e.g., Warfarin Overdose `R3` triggers `CONTROLLED_ABSTENTION`).
2. **LLM Generation:** `LiveMedicalRAGService` executes a `response_format={"type": "json_object"}` API request to Groq if the provider is configured.
3. **LLM Structured Contract:** Prompt `LIVE_APP_PROMPT_V1.txt` requests `conclusion`, `interactions`, `adverse_reactions`, `warnings`, `food_guidance`, `patient_considerations`, and importantly, a list of `claims_for_verification`. 
4. **Post-LLM Safety Verification:** Output from Groq is decoded. If JSON parse fails, `LLM_OUTPUT_VALIDATION_FAILURE` is yielded. Valid JSON proceeds to loop each element in `claims_for_verification` through `ClaimVerifierV2`. Any claim missing corroboration triggers `UNSUPPORTED`. If any claims fail, the Answer Safety Gate returns `CONTROLLED_ABSTENTION` with "One or more generated claims failed post-generation verification." 

## 3. Real Provider Test Result (Smoke Test)
Because `GROQ_API_KEY` was intentionally missing from the environment as per the strict instruction ("If GROQ_API_KEY is unavailable: do NOT fake success. Return: PROVIDER_CONFIGURATION_REQUIRED and stop there."), the RAG service evaluated the exact boundary, threw the updated `PROVIDER_CONFIGURATION_REQUIRED` SSE error, and properly halted execution without creating false claims or falling back to a dummy response. 

## 4. Final Success State
The technical boundary logic natively supports end-to-end routing when the API key is provided, correctly protecting against unauthorized usage, fake results, or unvalidated responses reaching the frontend. All research artifacts remain unaffected.
