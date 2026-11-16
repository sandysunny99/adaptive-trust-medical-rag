feat(nvidia): separate NVIDIA LLM and vision credentials; parse vision output strictly

The researcher's NVIDIA work (NVIDIA_VISION_SCHEMA_REMEDIATION_2026-10-12):

- app.py: the NVIDIA text model and the NVIDIA vision/OCR model take their own key, model and
  base URL (NVIDIA_LLM_* and NVIDIA_OCR_*/NVIDIA_VISION_*), each falling back to NVIDIA_API_KEY.
- model_registry.py: the NVIDIA model counts as configured with either NVIDIA_LLM_API_KEY or
  NVIDIA_API_KEY.
- openai_vision_backend.py: the request carries the exact JSON schema and
  response_format json_object. The reply is accepted only as one JSON object, one JSON object
  in a single code fence, or the observed NVIDIA bullet format; it is then validated
  (candidate_medications required, typed fields). Prose, embedded or trailing JSON, nested
  fences, malformed JSON and schema violations fail closed with SCHEMA_ERROR. A reply without
  candidate_medications is now rejected instead of read as no medications.
- tests/providers/test_vision_backend.py: 15 new cases for those paths.

Without this, the committed build rejected the vision model's fenced reply for the synthetic
prescription image (VISION_EXTRACTION_ERROR on 2026-10-18).

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
