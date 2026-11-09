# Prescription Image Architecture V1

## Architectural Principle
The Vision/OCR model is an **extraction** component, NOT a **medical reasoning** engine. The existing Adaptive Trust-Aware Evidence Control Layer must not be bypassed. 

## Processing Pipeline
1. **Upload**: User provides an image (`POST /api/v1/analyze/prescription`).
2. **Validation & Security**: Server blocks invalid formats, extreme sizes, and corrupted files. Computes SHA256 hashes of original and preprocessed images.
3. **Extraction**: `VisionLLMProvider` or `OCRProvider` extracts medication names and outputs them with a `confidence` level (e.g., HIGH, MEDIUM, LOW, UNCERTAIN).
4. **User Confirmation**: The extraction pipeline pauses. The user is presented with the candidates and must explicitly confirm, edit, or reject the extracted medications.
5. **Convergence**: Confirmed medications flow into the *exact same* RAG pipeline as text-input:
   - RxNorm Normalization
   - Hybrid Evidence Retrieval
   - Trust Scoring & Security Analysis
   - Pre-LLM Eligibility Gate
   - Text LLM Generation (NVIDIA or Groq)
   - Claim & Citation Verification
   - Post-LLM Safety Gate
   - Final Verified Answer

## Model Role Separation
- **TextLLMProvider**: Dedicated strictly to medical reasoning and synthesis.
- **VisionLLMProvider**: Dedicated to extracting text and reasoning about layout from an image.
- **OCRProvider**: Pure text extraction engine (e.g., `nemotron-ocr-v1`).
