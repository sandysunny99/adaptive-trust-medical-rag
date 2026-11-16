# Forensic Remediation Report: NVIDIA Vision Output Schema Resolution

**Date:** 2026-10-12  
**Repository:** `sandysunny99/adaptive-trust-medical-rag`  
**Base Commit (origin/main):** `91c853776ff7085faaaf25abdfbefa157dd55558`  
**Active Remediation Branch:** `fix/nvidia-vision-output-schema`  
**Status of Working Tree:** Uncommitted changes isolated on feature branch (`main` untouched)  

---

## 1. Root Cause Analysis of Live Vision Output Failure

During Stage E live integration validation on merged commit `91c8537`, submitting a synthetic prescription image to `POST /api/v1/analyze/prescription` resulted in:
`[error] {'code': 'VISION_EXTRACTION_ERROR', 'message': 'Vision extraction failed: Vision provider failed to return valid JSON'}`

### Forensic Diagnosis
1. **Model & Endpoint Invocation:** The real NVIDIA NIM endpoint (`https://integrate.api.nvidia.com/v1/chat/completions`) and model (`meta/llama-3.2-11b-vision-instruct`) were reached successfully (HTTP 200).
2. **Medication Extraction Performance:** The vision model accurately transcribed the synthetic prescription image (`"Rx: Warfarin 5mg - Take 1 tablet daily \n Aspirin 81mg - Take 1 tablet daily"`) and correctly identified the candidate drugs:
   * Warfarin (HIGH confidence)
   * Aspirin (HIGH confidence)
3. **Response Schema Mismatch:**
   * In `OpenAIVisionBackend.extract_medications`, the outbound request payload omitted the `"response_format": {"type": "json_object"}` parameter.
   * The system and user prompts lacked an explicit JSON schema template, merely requesting the model to "respond strictly in JSON format matching the requested schema".
   * In the absence of enforced JSON mode or schema definition, `meta/llama-3.2-11b-vision-instruct` returned structured conversational Markdown bullet points rather than raw JSON:
     ```markdown
     The image contains text that reads:

     "Rx
     Warfarin 5mg - Take 1 tablet daily
     Aspirin 81mg - Take 1 tablet daily"

     Based on the provided text, the following medication names are extracted:

     * Warfarin: Raw text - "Warfarin", Normalized generic name - "Warfarin", Confidence - HIGH
     * Aspirin: Raw text - "Aspirin", Normalized generic name - "Aspirin", Confidence - HIGH

     The full raw transcribed text of the image is:

     "Rx
     Warfarin 5mg - Take 1 tablet daily
     Aspirin 81mg - Take 1 tablet daily"
     ```
   * `OpenAIVisionBackend` executed `json.loads(cleaned)`, which failed with `JSONDecodeError("Expecting value: line 1 column 1")`, raising `ModelExecutionError` with `FailureClass.SCHEMA_ERROR`.

---

## 2. Implementation & Remediation Architecture

The remediation was implemented following Option A (provider boundary structured output enforcement) and Option B (defense-in-depth deterministic normalization fallback), preserving fail-closed security and medication safety invariants:

### Option A: Provider Boundary Enforcement
1. **JSON Mode Enabled:** Added `"response_format": {"type": "json_object"}` to the OpenAI-compatible chat completion payload.
2. **Explicit Schema Framing:** Updated `system_prompt` and `user_prompt` with an explicit JSON schema template:
   ```json
   {
     "raw_text": "<full transcribed text>",
     "candidate_medications": [
       {"raw_text": "<exact medication text>", "normalized_text": "<generic name or null>", "confidence": "HIGH|MEDIUM|LOW|UNCERTAIN"}
     ],
     "warnings": []
   }
   ```
   Testing against NVIDIA NIM confirmed that `meta/llama-3.2-11b-vision-instruct` natively respects this format and immediately emits pure, unadorned JSON.

### Option B: Deterministic Normalization Fallback
Implemented `_parse_and_validate_vision_response(content: str) -> dict`:
1. Strips conventional markdown code fences (```` ```json ... ``` ```` or ```` ``` ... ``` ````).
2. Parses canonical JSON directly if valid.
3. Searches for an embedded JSON block `{ ... }` within commentary if prose surrounds it.
4. **Deterministic Structured Bullet Parser:**
   Matches the exact observed NVIDIA NIM format:
   `r'^\s*[\*\-]\s*(?:(?P<label>[^:\n]+):\s*)?Raw text\s*-\s*["\']?(?P<raw>[^"\',\n]+)["\']?,\s*Normalized generic name\s*-\s*["\']?(?P<norm>[^"\',\n]+)["\']?,\s*Confidence\s*-\s*(?P<conf>[A-Za-z_]+)\s*$'`
   - Validates candidate `raw_text` length and presence.
   - Maps confidence strictly to `ExtractionConfidence` enum; unparseable values fall back to `UNCERTAIN` (never elevated).
   - Extracts transcription text from designated quotation blocks.
   - Appends audit warning: `"Normalized from structured markdown response"`.
5. **Fail-Closed Guarantee:**
   - Free-form narrative or arbitrary prose that does not conform to the schema is deterministically rejected with `FailureClass.SCHEMA_ERROR`.
   - No unrestricted regular expressions or fuzzy keyword matching are permitted to manufacture medication candidates from unstructured text.

---

## 3. Preservation of Safety Invariants

- **Medication Candidates vs. Identity:** Extracted items remain unconfirmed candidates.
- **Mandatory User Confirmation:** The pipeline always pauses at `confirmation_required` (`asyncio.Event`) and requires explicit confirmation via `POST /api/v1/analyze/{request_id}/confirm` before proceeding.
- **RxNorm Canonicalization:** Remains an independent, decoupled step. Unresolvable medications (`SyntheticUnknownDrug999`) trigger `NORMALIZATION_ERROR` and halt execution without hallucinating RxCUIs.
- **Component Isolation:** Vision model (`meta/llama-3.2-11b-vision-instruct`) remains completely isolated from answer LLMs (`nemotron-3-super-120b`, `gpt-oss-120b`), dense embeddings (`all-MiniLM-L6-v2`), and claim verification (`PubMedBERT-MNLI-MedNLI`).
- **Vision Provenance:** Full provenance recorded in app state (`vision_provider="nvidia_vision"`, `vision_model="meta/llama-3.2-11b-vision-instruct"`, original image SHA-256 hash, candidate IDs `ocr-0`, `ocr-1`).

---

## 4. Verification Evidence & Test Execution

### 4.1 Focused Vision & Prescription Regression Tests (27/27 PASSED)
Executed under CI test configuration (`$env:TESTING="1"`):
* `tests/providers/test_vision_backend.py`: **21 passed**
  * `test_1_successful_structured_extraction`: Canonical JSON -> PASS
  * `test_2_invalid_api_key`: 401 AUTHENTICATION -> PASS
  * `test_3_missing_api_key`: AUTHENTICATION -> PASS
  * `test_4_malformed_json`: SCHEMA_ERROR -> PASS
  * `test_5_schema_failure`: missing array -> PASS
  * `test_6_provider_timeout`: TIMEOUT -> PASS
  * `test_7_http_5xx`: 500 TRANSIENT_PROVIDER -> PASS
  * `test_8_rate_limit`: 429 RATE_LIMIT -> PASS
  * `test_9_malicious_image_text`: prompt injection text transcribed without obeying -> PASS
  * `test_10_multiple_medication_candidates`: 2 candidates -> PASS
  * `test_11_low_confidence_candidate`: LOW confidence preserved -> PASS
  * `test_12_empty_extraction`: 0 candidates -> PASS
  * `test_13_oversized_image_handling`: rejected by ImageValidator -> PASS
  * `test_14_invalid_image_handling`: rejected by ImageValidator -> PASS
  * `test_15_markdown_code_fence_json`: JSON in code fence parsed -> PASS
  * `test_16_observed_markdown_bullet_format`: exact NVIDIA NIM bullet format parsed with warnings -> PASS
  * `test_17_arbitrary_prose_fails_closed`: narrative text fails closed with SCHEMA_ERROR -> PASS
  * `test_18_empty_response_fails_closed`: empty response fails with SCHEMA_ERROR -> PASS
  * `test_19_unparseable_confidence_maps_safely`: unknown confidence maps to UNCERTAIN -> PASS
  * `test_20_prompt_injection_in_image_treated_as_literal`: preserved as literal text with LOW confidence -> PASS
  * `test_21_response_format_json_object_present_in_payload`: verifies outbound JSON mode payload -> PASS
* `tests/api/test_prescription_vision_e2e.py`: **1 passed**
* `tests/e2e/test_v6_c6_image_confirmation_rxnorm.py`: **5 passed**

### 4.2 Real NVIDIA Vision Provider Execution (`TESTING != 1`)
* Target: `meta/llama-3.2-11b-vision-instruct` on `https://integrate.api.nvidia.com/v1`
* Synthetic Fixture: Synthetic prescription image (Warfarin 5mg + Aspirin 81mg, zero PHI)
* Live Result:
  ```
  Sending synthetic image to NVIDIA Vision NIM...
  SUCCESS! Candidates extracted:
    raw_text: Warfarin, norm: Warfarin, conf: ExtractionConfidence.HIGH
    raw_text: Aspirin, norm: Aspirin, conf: ExtractionConfidence.HIGH
  ```
* Schema Validation: Accepted directly as canonical JSON (no fallback required).

### 4.3 Full Live Application Flow (Prescription -> Vision -> Confirmation -> RxNorm -> Live RAG)
Executed live across the entire pipeline:
1. `POST /api/v1/analyze/prescription` -> HTTP 200 OK (`request_id="97117247-8f24-4156-a85d-efa77f60dac0"`).
2. Live NVIDIA NIM vision extraction emitted `medication_candidates_extracted` (`Warfarin`, `Aspirin`, confidence `HIGH`).
3. Pipeline emitted `confirmation_required` and entered waiting state.
4. `POST /api/v1/analyze/{request_id}/confirm` confirmed `Warfarin` and `Aspirin`.
5. Sanitizer accepted 2 drugs.
6. RxNorm normalized `Warfarin` (RxCUI 11289) and `Aspirin` (RxCUI 1191).
7. Hybrid retrieval fetched 14 chunks from OpenFDA, DailyMed, and PubMed.
8. Security gates evaluated `ALLOW`.
9. Trust scorer produced score `0.9375` (eligible).
10. NVIDIA Nemotron-3 Super 120B generated evidence-grounded answer.
11. Real `PubMedBERT-MNLI-MedNLI` verified claims as `SUPPORTED`.
12. Final `answer` emitted with `gate_decision="release"` and 27 SSE events streamed cleanly.

---

## 5. Test Status Matrix

| Test / Flow | Test Mode | Status | Notes |
|---|---|---|---|
| **Vision Unit Tests (14 existing)** | Offline Mock | **`PASS`** | All existing assertions preserved |
| **Vision Markdown & Code Fence Tests (15-21)** | Offline Mock | **`PASS`** | Covers code fences, bullets, fail-closed prose, injection |
| **Prescription Vision Integration (`test_c5`)** | Offline Mock | **`PASS`** | Endpoint responds HTTP 200 |
| **RxNorm Confirmation E2E (`test_v6_c6`)** | CI / AsyncClient | **`PASS`** | 5/5 passed; confirms confirmation -> rxnorm flow |
| **Real NVIDIA NIM Direct Extraction** | Live Provider | **`PASS`** | Returns JSON, extracts Warfarin + Aspirin (HIGH) |
| **Real Live End-to-End Prescription Pipeline** | Live Provider | **`PASS`** | Complete flow to gate release (27 SSE events) |
| **Unresolvable Medication Rejection** | Live Provider | **`PASS`** | Fails closed with NORMALIZATION_ERROR |

---

## 6. Files Changed & Diff Summary

```
 src/adaptive_trust_medical_rag/llm_backend/openai_vision_backend.py | 242 ++++++++++++++++++---
 tests/providers/test_vision_backend.py                               | 122 +++++++++++
 2 files changed, 316 insertions(+), 48 deletions(-)
```

1. `src/adaptive_trust_medical_rag/llm_backend/openai_vision_backend.py`:
   * Enabled `"response_format": {"type": "json_object"}`.
   * Specified explicit JSON schema in system and user prompts.
   * Implemented `_parse_and_validate_vision_response` with code fence cleaning, direct JSON parse, embedded JSON extraction, and strict bullet list fallback.
   * Validated candidate structure, raw_text lengths, and enum values.
2. `tests/providers/test_vision_backend.py`:
   * Added 7 regression tests covering code fences, structured bullet formats, arbitrary prose failure, empty responses, unparseable confidence, prompt injection, and outbound JSON mode payload validation.

---

## 7. Research Integrity & Codebase State

* **Main Branch Intact:** Direct changes to `main` were strictly prohibited; changes reside exclusively on branch `fix/nvidia-vision-output-schema` and remain uncommitted.
* **Research Artifacts Untouched:** All evaluation datasets, manifests, prompts, and evaluation outputs in `experiments/` and `reports/audit/` remain intact and uncorrupted.
* **Zero PHI & Zero Secrets:** Pure synthetic image data used; Gitleaks, Bandit, and Ruff all passed cleanly with 0 alerts.
