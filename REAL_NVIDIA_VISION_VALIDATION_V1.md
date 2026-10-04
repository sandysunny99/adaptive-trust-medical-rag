# Real NVIDIA Vision Validation v1

## Scope
Validation of `LiveMedicalRAGService` correctly invoking `OpenAIVisionBackend` (acting as the NVIDIA vision provider using the OpenAI-compatible REST schema).

## Environment
- Provider: `nvidia`
- Authentication: Securely handled via environment variables
- Live Vision Requests recorded: 1

## Results
- **Endpoint connectivity**: Verified via `https://integrate.api.nvidia.com/v1/chat/completions`
- **Request Formatting**: Payload formatted properly including Base64-encoded image URLs.
- **Handling of Responses**: Successful mapping from the model's text response to a JSON `ExtractionResult`.
- **System boundary**: Extraction successfully stops at `confirmation_required` event and prevents the LLM or RxNorm from interpreting raw OCR values automatically.

## Known Limitations
- "Vision is medically accurate" is NOT claimed.
- Pipeline guarantees only that structured medication candidate data is collected and presented to a human for confirmation.
