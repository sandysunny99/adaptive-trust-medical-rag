# NVIDIA Vision Extraction v1

## Overview
This document outlines the extraction configuration for the `meta/llama-3.2-11b-vision-instruct` model on the NVIDIA integrate API.

## Configuration
- Provider: `nvidia_vision`
- Endpoint: `https://integrate.api.nvidia.com/v1/chat/completions`
- Authentication: Bearer token via `NVIDIA_API_KEY`

## Extraction Protocol
1. Image is validated via Pillow (size, mime, format, decode verify).
2. Hash (SHA-256) is recorded for provenance.
3. Strict system prompt instructs the model to only extract visible text and medication candidates.
4. Response is structured JSON enforcing a `MedicationCandidate` schema containing `raw_text`, `normalized_text`, and `confidence` enum (`HIGH`, `MEDIUM`, `LOW`, `UNCERTAIN`).
5. Output is funneled directly into the Confirmation Boundary (V6-C3), pausing the pipeline and preventing auto-normalization or RAG.

## Status
- Unit tests: PASS
- Integration tests: PASS
- Security constraints: ENFORCED
