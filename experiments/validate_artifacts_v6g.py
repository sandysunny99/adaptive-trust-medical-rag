import os
import json

out_dir = os.path.abspath("experiments/track_a_abstract_enriched_reannotation_v1")

def load_json(name):
    path = os.path.join(out_dir, name)
    if not os.path.exists(path): return None
    with open(path, "r", encoding="utf-8") as f: return json.load(f)

# Load data
registry = load_json("COGNEE_GATE5_CORRECTION06G_PROTOCOL_SOURCE_REGISTRY.json")
ledger = load_json("COGNEE_GATE5_CASE_MATRIX_LEDGER.json")
expectation_audit = load_json("COGNEE_GATE5_CORRECTION06G_EXPECTATION_AUDIT.json")
final_status = load_json("COGNEE_GATE5_CORRECTION06G_FINAL_STATUS.json")

errors = []

if not registry: errors.append("Missing PROTOCOL_SOURCE_REGISTRY")
else:
    auth_src = registry.get("authoritative_source", {})
    if not auth_src.get("path"): errors.append("No authoritative source path defined")
    if auth_src.get("sha256") == "UNKNOWN": errors.append("Authoritative source is missing or unhashed")

if not ledger: errors.append("Missing CASE_MATRIX_LEDGER")
else:
    # Ensure no expected outcome source is "PROTOCOL_MATRIX_V2" since we rooted it
    for c in ledger:
        if c.get("expected_outcome_source") == "PROTOCOL_MATRIX_V2":
            errors.append(f"Case {c['case_id']} still uses generic PROTOCOL_MATRIX_V2 as source")

if not final_status: errors.append("Missing FINAL_STATUS")
else:
    if final_status.get("full_contract_reproducibility") == "FULL_CONTRACT_EXACT_MATCH":
        errors.append("Validation failure: claimed FULL_CONTRACT_EXACT_MATCH while actual_cognee_result_id is UNAVAILABLE.")
    if final_status.get("pos02", {}).get("protocol_expected_contaminated_outcome") != "NOT_DEFINED_IN_SOURCE":
        errors.append("Validation failure: POS-02 conditional behavior should be NOT_DEFINED_IN_SOURCE")

if errors:
    print("VALIDATION V6G FAILED WITH ERRORS:")
    for e in errors: print(" -", e)
    exit(1)
else:
    print("Validation V6G Complete. Zero conflicts.")
