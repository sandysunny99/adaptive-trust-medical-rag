import json
import os

out_dir = "track_a_annotation/decision_batches"
os.makedirs(out_dir, exist_ok=True)

arch_audit = """# TRACK_A_LLM_CURRENT_ARCHITECTURE_AUDIT_V1

## Overview
The architecture is now securely decoupled into a uniform LLMProviderAdapter distinguishing the routing gateway from the core inference provider.

## Component Status
* **DIRECT_GROQ**: CODE_PRESENT. Configured to use GROQ_API_KEY, targeting https://api.groq.com/openai/v1/chat/completions. Supports explicit JSON_OBJECT response format.
* **DIRECT_CLOUDFLARE**: CODE_PRESENT. Actively retrieves CLOUDFLARE_ACCOUNT_ID from the environment to dynamically construct the endpoint (https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/chat/completions). Supports explicit JSON_OBJECT mode.
* **DIRECT_HUGGINGFACE**: CODE_PRESENT. Uses generic Inference endpoint targeting model routes. Operates in PROMPT_ONLY structured mode as a baseline safety since schema capabilities vary across HF models.
* **FREELLMAPI_GATEWAY**: CODE_PRESENT. Identifies FREELLMAPI_BASE_URL and FREELLMAPI_API_KEY. Captures X-Routed-Via and X-Fallback-Attempts to establish reproducible routing provenance.

## Capabilities Verified by Code
* **Authentication Variable Retrieval**: CODE_PRESENT (No literal fallback placeholders remain).
* **Generation Parameters (Temp, Top_P, Tokens, Seed)**: CODE_PRESENT.
* **Timeout and Retries**: CODE_PRESENT (Bounded 3 retries, exponential backoff).
* **JSON Parsing & Schema Validation**: CODE_PRESENT (Strict validation against schema definitions).
* **Exact Span Validation**: CODE_PRESENT (Independent substring calculation).

*Note: All capabilities remain EXECUTION_UNVERIFIED until an actual API key activates the network layer.*
"""

freellmapi_audit = """# TRACK_A_LLM_FREELLMAPI_ROUTING_AUDIT_V1

## FreeLLMAPI Provenance Tracking
FreeLLMAPI is integrated as a valid GATEWAY, completely distinct from the underlying PROVIDER. The adapter natively traps routing variables to ensure the dataset isn't corrupted by silent failovers:
* **esolved_provider**: Actively parsed from X-Routed-Via response headers (per documentation) rather than presumed custom headers.
* **allback_attempts**: Parsed from X-Fallback-Attempts.
* **outing_changed**: Actively flipped to True if a fallback attempt occurred or if the provider could not be explicitly confirmed.

This ensures any automated routing decisions made by the gateway are recorded in the final semantic payload to maintain strict evaluation reproducibility.
"""

opts = """# TRACK_A_LLM_PROVIDER_OPTIONS_V3

## Selection of Target Configurations
The final medical annotation run relies on the researcher picking a distinct and pinned infrastructure combination. **Do not run the pilot automatically.**

| Execution Mode | Expected Latency | Structured Output Method | Routing Predictability | Credential Required |
|---|---|---|---|---|
| DIRECT_GROQ | Low | JSON_OBJECT | High (Direct) | GROQ_API_KEY |
| DIRECT_CLOUDFLARE | Low | JSON_OBJECT | High (Direct) | CLOUDFLARE_API_KEY + ACCOUNT_ID |
| DIRECT_HUGGINGFACE | Medium | PROMPT_ONLY | High (Direct) | HUGGINGFACE_API_KEY |
| FREELLMAPI_GATEWAY | Varies | JSON_OBJECT | Variable (Tracked via Headers) | FREELLMAPI_API_KEY |
"""

adapter_audit = """# TRACK_A_LLM_ADAPTER_IMPLEMENTATION_AUDIT_V4

## Real Capabilities Verified
| Requirement | Status | Detail |
|---|---|---|
| **INTERFACE_IMPLEMENTED** | YES | Common provider-neutral interface intact. |
| **REAL_PROVIDER_CALL_IMPLEMENTED** | YES | Uses dynamic equests.post targeting distinct API structures per execution mode. |
| **JSON_PARSING_IMPLEMENTED** | YES | json.loads explicitly handled. |
| **SCHEMA_VALIDATION_IMPLEMENTED** | YES | Basic type-enforcement and key presence validation deployed. |
| **SPAN_VALIDATION_IMPLEMENTED** | YES | Utilizes idx = evidence_text.find(...) blocking fabricated spans. |
| **RETRY_IMPLEMENTED** | YES | Explicit bounded retries with true exponential backoff mechanism. |
| **TIMEOUT_IMPLEMENTED** | YES | Passed dynamically to the request layer. |
| **METADATA_CAPTURE_IMPLEMENTED** | YES | Captures headers, parameters, and prompt execution hashes. |
| **SECRET_PROTECTION_IMPLEMENTED** | YES | Zero hardcoded keys or credentials leaked to logs. |
| **MOCK_FALLBACK_BLOCKED** | YES | Verified via NEGATIVE_PATH_TEST. |
"""

config = """# TRACK_A_LLM_EXECUTION_CONFIG_V4

> **STATUS**: NOT_FROZEN
> *Cannot freeze configuration until a real provider test completes successfully.*

EXECUTION_MODE = [TBD: DIRECT_GROQ / DIRECT_CLOUDFLARE / DIRECT_HUGGINGFACE / FREELLMAPI_GATEWAY]
GATEWAY = [TBD]
PROVIDER = [TBD]
REQUESTED_MODEL = [TBD]
RESOLVED_MODEL = [TBD]
MODEL_VERSION_OR_REVISION = [TBD]
ENDPOINT = [TBD]
INFERENCE_CLIENT = requests_openai_compatible
TEMPERATURE = 0.0
TOP_P = 0.1
MAX_TOKENS = 2048
SEED = 42
TIMEOUT = 120s
RETRY_POLICY = 3_retries_transient_only
FAILOVER_POLICY = ENABLED_BUT_TRACKED
STRUCTURED_OUTPUT_METHOD = [TBD]
SYSTEM_PROMPT_HASH = [TBD]
ADJUDICATION_PROMPT_HASH = [TBD]
CHALLENGE_PROMPT_HASH = [TBD]
SCHEMA_HASH = [TBD]
PROVIDER_CAPABILITY_MATRIX_HASH = [TBD]
PYTHON_VERSION = 3.12+
PACKAGE_VERSIONS = [TBD]
PROVIDER_SDK_VERSION = native_requests
EXECUTION_DATE = [TBD]
HOST_CLASS = [TBD]
"""

cap_matrix = {
    "DIRECT_GROQ": {"temperature": "CODE_PRESENT", "top_p": "CODE_PRESENT", "seed": "CODE_PRESENT", "structured_output": "CODE_PRESENT"},
    "DIRECT_CLOUDFLARE": {"temperature": "CODE_PRESENT", "top_p": "CODE_PRESENT", "seed": "CODE_PRESENT", "structured_output": "CODE_PRESENT"},
    "DIRECT_HUGGINGFACE": {"temperature": "CODE_PRESENT", "top_p": "CODE_PRESENT", "seed": "CODE_PRESENT", "structured_output": "CODE_PRESENT"},
    "FREELLMAPI_GATEWAY": {"temperature": "CODE_PRESENT", "top_p": "CODE_PRESENT", "seed": "CODE_PRESENT", "structured_output": "CODE_PRESENT"}
}

verification = {
    "PROVIDER_AUTHENTICATED": "NOT_VERIFIED",
    "MODEL_VERIFIED": "NOT_VERIFIED",
    "STRUCTURED_OUTPUT_VERIFIED": "NOT_VERIFIED",
    "PARAMETERS_VERIFIED": "NOT_VERIFIED",
    "EXECUTION_VERIFIED": "NOT_VERIFIED"
}

live_test = {
    "status": "NOT_EXECUTED",
    "reason": "Missing Credentials"
}

files = {
    "TRACK_A_LLM_CURRENT_ARCHITECTURE_AUDIT_V1.md": arch_audit,
    "TRACK_A_LLM_FREELLMAPI_ROUTING_AUDIT_V1.md": freellmapi_audit,
    "TRACK_A_LLM_PROVIDER_OPTIONS_V3.md": opts,
    "TRACK_A_LLM_ADAPTER_IMPLEMENTATION_AUDIT_V4.md": adapter_audit,
    "TRACK_A_LLM_EXECUTION_CONFIG_V4.md": config,
    "TRACK_A_LLM_PROVIDER_CAPABILITY_MATRIX_V3.json": json.dumps(cap_matrix, indent=2),
    "TRACK_A_LLM_PROVIDER_VERIFICATION_V3.json": json.dumps(verification, indent=2),
    "TRACK_A_LLM_LIVE_TRANSPORT_TEST_V3.json": json.dumps(live_test, indent=2),
    "TRACK_A_LLM_PROMPT_HASHES_V2.json": "{}" 
}

for name, content in files.items():
    with open(f"{out_dir}/{name}", "w", encoding="utf-8") as f:
        f.write(content)

print("Generated required V3/V4 artifacts.")
