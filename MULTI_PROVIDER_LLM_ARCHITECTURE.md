# Multi-Provider LLM Architecture

## Abstract
The Adaptive Trust Medical RAG platform now supports a normalized multi-provider architecture using OpenAI-compatible adapters. By placing the API surface behind `LiveProviderRouter`, we create a clean separation of concerns:
- **Medical Trust & Safety**: Evaluated natively upstream/downstream regardless of provider.
- **LLM Engine**: Generates JSON payloads conforming to `ClaimVerifierV2` schemas.

## Current Supported Providers
- **NVIDIA (Primary Default)**: Uses `nvidia/nemotron-3-super-120b-a12b` via NIM.
- **Groq (Secondary / Fallback)**: Uses `openai/gpt-oss-120b`.

## Fallback Routing Policy
Automatic failover triggers exclusively on infrastructure-level anomalies mapping to:
- `FailureClass.TIMEOUT`
- `FailureClass.NETWORK`
- `FailureClass.TRANSIENT_PROVIDER`
- `FailureClass.RATE_LIMIT`
- `FailureClass.AUTHENTICATION`

Failovers will **never** trigger for semantic failures (`FailureClass.APPLICATION_SEMANTIC` or `SCHEMA_ERROR`). If safety verification fails, the pipeline fails closed in a controlled abstention.
