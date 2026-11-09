# Hugging Face Integration Decision

## Analysis
The Hugging Face Inference API was previously marked as "incompatible" because its adapter (HuggingFaceBackend) only implemented plain text generate().

**Provider Capability**: Hugging Face's 1/chat/completions endpoint does support OpenAI formatting.
**Structured Output Support**: While HF technically supports JSON schema formatting on certain models, live tests targeting pi-inference.huggingface.co/models/.../v1 returned network failures (getaddrinfo failed), and the free tier heavily restricts complex schema generation queries.

## Decision
**KEEP OUT - INCOMPATIBLE**
The limitation is a combination of free-tier reliability, network blocking on the inference endpoint, and inconsistent structured JSON schema parsing across the free models. Integrating it as a fallback would destabilize the medical safety gates.
