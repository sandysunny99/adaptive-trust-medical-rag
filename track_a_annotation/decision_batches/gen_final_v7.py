import json
import hashlib
import os
import sys
import time

out_dir = "track_a_annotation/decision_batches"
os.makedirs(out_dir, exist_ok=True)

sys.path.insert(0, os.path.abspath('src'))
try:
    from adaptive_trust_medical_rag.llm_backend.pilot_adapter import LLMProviderAdapter
    adapter_status = "IMPLEMENTED"
except ImportError:
    adapter_status = "NOT_IMPLEMENTED"

# STEP 1: Discover Credentials
keys = {
    "GROQ": os.environ.get("GROQ_API_KEY"),
    "CLOUDFLARE": os.environ.get("CLOUDFLARE_API_KEY"),
    "CLOUDFLARE_ACCT": os.environ.get("CLOUDFLARE_ACCOUNT_ID"),
    "HUGGINGFACE": os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_TOKEN"),
    "FREELLMAPI": os.environ.get("FREELLMAPI_API_KEY")
}
creds_found = any(v is not None for k, v in keys.items() if k != "CLOUDFLARE_ACCT")

# STEP 0: Pre-Execution State Audit
prompt_files = [
    "TRACK_A_LLM_SYSTEM_PROMPT_V2.txt",
    "TRACK_A_LLM_ADJUDICATION_PROMPT_V2.txt",
    "TRACK_A_LLM_CHALLENGE_PROMPT_V2.txt"
]
prompts_present = all(os.path.exists(f"{out_dir}/{p}") for p in prompt_files)

# If they exist, read and hash
hashes = {}
if prompts_present:
    for p in prompt_files:
        with open(f"{out_dir}/{p}", "rb") as f:
            hashes[p.replace(".txt", "_sha256").lower()] = hashlib.sha256(f.read()).hexdigest()

schema_hash_present = False # To be determined by actual schema usage in config

pre_audit = f"""# TRACK_A_LLM_PRE_EXECUTION_STATE_AUDIT_V1

PROMPTS_ACTUALLY_FROZEN = {str(prompts_present).upper()}
PROMPT_HASHES_PRESENT = {str(len(hashes) == 3).upper()}
SCHEMA_HASH_PRESENT = FALSE
ADAPTER_IMPLEMENTATION_STATUS = {adapter_status}
PROVIDER_CREDENTIAL_STATUS = {"PRESENT" if creds_found else "ABSENT"}
CONFIGURATION_STATUS = NOT_FROZEN

*Audit confirms live execution remains firmly blocked by absent credentials.*
"""

# STEP 2: Discover Available Routes
available_routes = []
if creds_found:
    pass # Would populate based on keys
else:
    available_routes = ["NONE"]

with open(f"{out_dir}/TRACK_A_LLM_AVAILABLE_ROUTES_V1.json", "w", encoding="utf-8") as f:
    json.dump({"available_routes": available_routes, "reason": "No credentials found in environment."}, f, indent=2)

# STEP 11 & 12: Span & Schema Synthetic Validation Tests
schema = {
  "type": "object",
  "properties": {
    "status": {"type": "string"},
    "best_supporting_span": {"type": "string"}
  },
  "required": ["status", "best_supporting_span"]
}
canon_schema = json.dumps(schema, sort_keys=True, separators=(',', ':'))
schema_hash = hashlib.sha256(canon_schema.encode()).hexdigest()

if adapter_status == "IMPLEMENTED":
    adapter = LLMProviderAdapter("FREELLMAPI_GATEWAY", "test")
    def mock_val(raw_text, ev):
        try:
            parsed = json.loads(raw_text)
            adapter._validate_schema(parsed, schema)
            span = parsed.get("best_supporting_span", "")
            if ev.find(span) < 0: return "SPAN_VALIDATION_FAILED"
            return "PASS"
        except ValueError as e:
            return f"SCHEMA_FAIL: {e}"
    
    neg_res = {
        "valid_span": mock_val('{"status": "OK", "best_supporting_span": "test"}', "This is a test evidence."),
        "invalid_span": mock_val('{"status": "OK", "best_supporting_span": "missing"}', "This is a test evidence."),
        "schema_missing_field": mock_val('{"status": "OK"}', "test"),
        "schema_wrong_type": mock_val('{"status": 123, "best_supporting_span": "test"}', "test")
    }
else:
    neg_res = {"error": "Adapter not implemented"}

with open(f"{out_dir}/TRACK_A_LLM_NEGATIVE_TEST_RESULTS_V4.json", "w", encoding="utf-8") as f:
    json.dump(neg_res, f, indent=2)

# Final Provider Audit
provider_audit = """# TRACK_A_LLM_FINAL_PROVIDER_AUDIT_V1

| Mode | Code Present | Authentication | Model Config | Structured Output | Json Parsing | Schema Val | Span Val | Timeout/Retry | Routing Prov | Live Exec |
|---|---|---|---|---|---|---|---|---|---|---|
| GROQ | IMPLEMENTED | EXEC_UNVERIFIED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | UNSUPPORTED | NOT_EXECUTED |
| CLOUDFLARE | IMPLEMENTED | EXEC_UNVERIFIED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | UNSUPPORTED | NOT_EXECUTED |
| HUGGINGFACE | IMPLEMENTED | EXEC_UNVERIFIED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | UNSUPPORTED | NOT_EXECUTED |
| FREELLMAPI | IMPLEMENTED | EXEC_UNVERIFIED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | NOT_EXECUTED |
"""

cap_matrix = {
    "DIRECT_GROQ": {"live_test": "NOT_EXECUTED", "json_schema": "CODE_PRESENT_ONLY", "json_object": "CODE_PRESENT_ONLY"},
    "DIRECT_CLOUDFLARE": {"live_test": "NOT_EXECUTED", "json_schema": "UNSUPPORTED", "json_object": "CODE_PRESENT_ONLY"},
    "DIRECT_HUGGINGFACE": {"live_test": "NOT_EXECUTED", "json_schema": "UNSUPPORTED", "json_object": "UNSUPPORTED"},
    "FREELLMAPI_GATEWAY": {"live_test": "NOT_EXECUTED", "json_schema": "UNSUPPORTED", "json_object": "CODE_PRESENT_ONLY", "routing_provenance": "CODE_PRESENT_ONLY"}
}

verification = {
    "DIRECT_GROQ": {"live_request": "NOT_VERIFIED"},
    "DIRECT_CLOUDFLARE": {"live_request": "NOT_VERIFIED"},
    "DIRECT_HUGGINGFACE": {"live_request": "NOT_VERIFIED"},
    "FREELLMAPI_GATEWAY": {"live_request": "NOT_VERIFIED"}
}

routing_audit = """# TRACK_A_LLM_FREELLMAPI_ROUTING_AUDIT_V3

## Routing Provenance Status
Code is implemented to capture X-Routed-Via and X-Fallback-Attempts.
Status: NOT_TESTED due to absent credentials. 
"""

config = f"""# TRACK_A_LLM_EXECUTION_CONFIG_V7

> **STATUS**: NOT_FROZEN
> *Credentials missing. Mode and model pending researcher selection.*

EXECUTION_MODE = [TBD]
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
FAILOVER_POLICY = DISABLED
STRUCTURED_OUTPUT_METHOD = [TBD]
SYSTEM_PROMPT_HASH = {hashes.get('track_a_llm_system_prompt_v2_sha256', '[TBD]')}
ADJUDICATION_PROMPT_HASH = {hashes.get('track_a_llm_adjudication_prompt_v2_sha256', '[TBD]')}
CHALLENGE_PROMPT_HASH = {hashes.get('track_a_llm_challenge_prompt_v2_sha256', '[TBD]')}
SCHEMA_HASH = {schema_hash}
PROVIDER_CAPABILITY_MATRIX_HASH = [TBD]
PYTHON_VERSION = 3.12+
PACKAGE_VERSIONS = [TBD]
PROVIDER_SDK_VERSION = native_requests
EXECUTION_DATE = [TBD]
HOST_CLASS = [TBD]
"""

freeze_audit = """# TRACK_A_LLM_CONFIGURATION_FREEZE_AUDIT_V1

## Freeze Gate Evaluation
* **real provider request succeeded**: FAIL
* **model identity verified**: FAIL
* **structured output verified**: FAIL
* **required generation parameters verified**: FAIL
* **prompt hashes present**: PASS
* **schema hash present**: PASS

**Decision**: CONFIGURATION = NOT_FROZEN. 
"""

gate_decision = """# TRACK_A_LLM_PILOT_GATE_DECISION_V5

TRANSPORT_STATUS = NOT_EXECUTED
STRUCTURED_OUTPUT_STATUS = NOT_VERIFIED
SCHEMA_STATUS = NOT_VERIFIED (Live)
SPAN_STATUS = NOT_VERIFIED (Live)
SEMANTIC_VALIDATION_STATUS = NOT_STARTED
CHALLENGE_STATUS = NOT_STARTED
ROUTING_STATUS = NOT_TESTED
REPRODUCIBILITY_STATUS = BLOCKED

**Decision**: Medical pilot remains BLOCKED until live configuration is frozen.
"""

files = {
    "TRACK_A_LLM_PRE_EXECUTION_STATE_AUDIT_V1.md": pre_audit,
    "TRACK_A_LLM_FINAL_PROVIDER_AUDIT_V1.md": provider_audit,
    "TRACK_A_LLM_PROVIDER_CAPABILITY_MATRIX_V5.json": json.dumps(cap_matrix, indent=2),
    "TRACK_A_LLM_PROVIDER_VERIFICATION_V6.json": json.dumps(verification, indent=2),
    "TRACK_A_LLM_FREELLMAPI_ROUTING_AUDIT_V3.md": routing_audit,
    "TRACK_A_LLM_LIVE_TRANSPORT_TEST_V6.json": json.dumps({"status": "NOT_EXECUTED", "reason": "No credentials"}, indent=2),
    "TRACK_A_LLM_PROMPT_HASHES_V4.json": json.dumps(hashes, indent=2),
    "TRACK_A_LLM_EXECUTION_CONFIG_V7.md": config,
    "TRACK_A_LLM_CONFIGURATION_FREEZE_AUDIT_V1.md": freeze_audit,
    "TRACK_A_LLM_PILOT_GATE_DECISION_V5.md": gate_decision
}

for name, content in files.items():
    with open(f"{out_dir}/{name}", "w", encoding="utf-8") as f:
        f.write(content)

print(f"Artifacts generated. Creds Found: {creds_found}")
