# NVIDIA Provider Integration

This document outlines the addition of the NVIDIA NIM Free Endpoint as a first-class LLM provider alongside Groq.

## Provider Details
- **Provider**: NVIDIA
- **Model**: `nvidia/nemotron-3-super-120b-a12b`
- **Endpoint**: `https://integrate.api.nvidia.com/v1`

## Implementation Overview
We've extended the LLM provider system to use an OpenAI-compatible abstraction layer:
1. `ProviderAdapter`: A unified Protocol defining `initialize`, `health_check`, `generate_structured`, `stream`, and error normalization.
2. `OpenAICompatibleBackend`: An adapter that works for both Groq and NVIDIA.
3. `LiveProviderRouter`: A new runtime router that sits between the application and the provider, enforcing explicit failover behavior based on normalized `FailureClass` signals.

## Structured Output & Evidence Verification
NVIDIA sits cleanly behind our existing verification pipeline. It must return JSON (via the `{"type": "json_object"}` request payload), which is then decoded and natively subjected to `ClaimVerifierV2`.

## Current Limitations
Currently, valid credentials have not been securely injected into the environment (`NVIDIA_API_KEY_PRESENT=False`). The system will correctly fail-closed with a 401 Unauthorized (`FailureClass.AUTHENTICATION`) if queried directly on a protected endpoint.
