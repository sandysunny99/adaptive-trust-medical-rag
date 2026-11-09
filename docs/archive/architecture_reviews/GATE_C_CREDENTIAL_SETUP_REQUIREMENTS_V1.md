# GATE C CREDENTIAL SETUP REQUIREMENTS

**Date:** 2026-10-03  

## Missing Prerequisite
Gate C Live Provider Validation cannot proceed without a valid API credential for the primary provider.

**Provider:** google  
**Model:** gemini-3.1-pro-preview  
**Required Environment Variable:** `GEMINI_API_KEY`  

## Setup Instructions
1. Obtain the API key for the required provider.
2. Inject the key into the host environment or a local `.env` configuration file readable by the runtime.
3. **Runtime Restart Requirement:** YES. The Antigravity agent or execution runtime must be restarted so that `os.environ` correctly inherits the new secret.

## Safe Verification Command
Use the following non-exposing command to verify the runtime has inherited the secret:
```python
import os
print("RUNTIME_SEES_CREDENTIAL:", "GEMINI_API_KEY" in os.environ and len(os.environ["GEMINI_API_KEY"]) > 0)
```

## Expected Post-Setup State
Upon successful verification, the Gate C preflight status will transition from `BLOCKED` to `READY`, authorizing minimal live provider connectivity tests.
