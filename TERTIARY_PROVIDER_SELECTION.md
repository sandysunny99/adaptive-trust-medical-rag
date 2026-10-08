# Tertiary Provider Selection

## Selection: Cloudflare Workers AI

## Rationale
To improve system resilience beyond Groq and NVIDIA, a tertiary provider is needed. 

1. **Compatibility**: Cloudflare's OpenAI-compatible endpoint flawlessly rendered the strict JSON schema required by the Answer Safety Gate during smoke tests.
2. **Reliability**: Cloudflare's edge network provides excellent uptime and low latency.
3. **Free-Tier**: The allocation (10,000 Neurons/day) is sufficient for a tertiary fallback role.
4. **Implementation Quality**: By utilizing the existing OpenAICompatibleBackend adapter, no custom boilerplate or maintenance burden is added to the repository.
