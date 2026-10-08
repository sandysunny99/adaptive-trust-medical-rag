import glob
import json
import os

files = [
    'FREE_LLM_PROVIDER_SELECTION_V2.md',
    'HUGGINGFACE_INTEGRATION_DECISION.md',
    'CLOUDFLARE_INTEGRATION_DECISION.md',
    'PROVIDER_COMPATIBILITY_AUDIT_V2.md',
    'TERTIARY_PROVIDER_SELECTION.md',
    'LIVE_PROVIDER_ROUTING_V3.md',
    'LIVE_PROVIDER_HEALTH_REPORT_V3.md',
    'LIVE_FAILOVER_VALIDATION_V3.md'
]

content = "# Consolidated Provider Decision Log V3\n\n"
for f in files:
    try:
        with open(f, 'r') as fp:
            content += f"---\n\n## Source: {f}\n\n{fp.read()}\n\n"
    except Exception as e:
        print(f"Error reading {f}: {e}")

# We will just print the content so the model can write it to an artifact
with open('temp_out.txt', 'w') as out:
    out.write(content)
