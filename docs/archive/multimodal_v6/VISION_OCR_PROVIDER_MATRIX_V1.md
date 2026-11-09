# Vision & OCR Provider Matrix V1

This document outlines the supported providers for the extraction phase of the image pipeline.

## Provider Roles

### VisionLLMProvider
Responsible for interpreting layout, handwriting, and printed text simultaneously. It outputs structured JSON containing candidate medications.
**NVIDIA Vision Models:**
- `meta/llama-3.2-11b-vision-instruct` (NVIDIA Free Endpoint) - *Primary prototype target*
- `meta/llama-3.2-90b-vision-instruct` (NVIDIA Free Endpoint)

### OCRProvider
A dedicated engine strictly for document text extraction and layout analysis.
**NVIDIA OCR Models:**
- `nemotron-ocr-v1` - *Intended for RAG document ingestion workflows (currently documented as a downloadable NIM, differing from standard chat-completions endpoint).*

### TextLLMProvider
Retained solely for medical reasoning and synthesis. No image data is passed to this provider.
- `nvidia/nemotron-3-super-120b-a12b`
- `openai/gpt-oss-120b` (Groq)

## Environment Configuration
```env
VISION_PROVIDER=nvidia
VISION_MODEL=meta/llama-3.2-11b-vision-instruct

TEXT_LLM_PROVIDER=nvidia
TEXT_LLM_MODEL=nvidia/nemotron-3-super-120b-a12b
```
