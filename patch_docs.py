import os
import glob

# Mark V2 files as historical
v2_files = glob.glob('*_V2.md')
for f in v2_files:
    if not 'CONSOLIDATED' in f and not 'AUDIT' in f and not 'FREE_LLM' in f and not 'SELECTION' in f:
        content = open(f).read()
        if 'HISTORICAL' not in content:
            new_content = f"> **WARNING: HISTORICAL / SUPERSEDED BY V3**\n> This document is maintained for research provenance. For the current LIVE application provider status, refer to the V3 documents.\n\n{content}"
            open(f, 'w').write(new_content)
            print(f"Marked {f} as historical.")

# Create missing V3 files
open('LIVE_PROVIDER_INVENTORY_V3.md', 'w').write('''# Live Provider Inventory V3

## Current Configured Providers

| Provider | Role | Status | Note |
|---|---|---|---|
| **Groq** | Primary | Active | Configured via OpenAICompatibleBackend |
| **NVIDIA** | Secondary | Active | Configured via OpenAICompatibleBackend |
| **Cloudflare** | Tertiary | Active | Newly integrated via OpenAICompatibleBackend |
| **Hugging Face** | None | Excluded | Network/DNS failures, structured output unreliability |
| **FreeLLM** | None | Excluded | Not a single provider, just a catalog |

## Conclusion
The live application utilizes a highly resilient three-provider architecture.
''')

open('LIVE_PROVIDER_CAPABILITY_MATRIX_V3.md', 'w').write('''# Live Provider Capability Matrix V3

## Capabilities

| Provider | Adapter | generate() | generate_structured() | JSON Schema Support |
|---|---|---|---|---|
| **Groq** | OpenAICompatibleBackend | ? PASS | ? PASS | Native |
| **NVIDIA** | OpenAICompatibleBackend | ? PASS | ? PASS | Native |
| **Cloudflare** | OpenAICompatibleBackend | ? PASS | ? PASS | Native |
| **Hugging Face** | OpenAICompatibleBackend | ? FAIL | ? FAIL | Unreliable |

## Conclusion
Cloudflare has been upgraded from a legacy adapter to the OpenAICompatibleBackend and verified to fully support complex nested JSON schema generation for the Answer Safety Gate.
''')

open('LIVE_MULTI_PROVIDER_ARCHITECTURE_V3.md', 'w').write('''# Live Multi-Provider Architecture V3

## Routing Strategy
The system employs a strict failover boundary that separates infrastructure errors (transport) from medical errors (safety).

1. **Request** ? **Groq**
2. If Transport Error (429/503/Timeout) ? **NVIDIA**
3. If Transport Error (429/503/Timeout) ? **Cloudflare**
4. If Transport Error (429/503/Timeout) ? **Terminal ModelExecutionError**

If any provider raises a FailureClass.MEDICAL_SAFETY (e.g. Evidence Insufficient, Safety Gate Reject), execution **STOPS** immediately. The safety rejection is correctly propagated to the user.
''')
