import json
import hashlib
import os
import sys

def main():
    print("Validating V1.2 Protocol...")
    
    # 1. Load Protocol
    protocol_path = "REAL_LLM_EVALUATION_PROTOCOL_V1_2.json"
    if not os.path.exists(protocol_path):
        print(f"FAIL: Protocol file {protocol_path} not found.")
        sys.exit(1)
        
    with open(protocol_path, "r", encoding="utf-8") as f:
        protocol = json.load(f)
        
    # 2. Check Dataset
    dataset_path = protocol["dataset"]["path"]
    if not os.path.exists(dataset_path):
        print(f"FAIL: Dataset {dataset_path} not found.")
        sys.exit(1)
        
    with open(dataset_path, "rb") as f:
        ds_raw = f.read()
    
    ds_hash = hashlib.sha256(ds_raw).hexdigest()
    expected_ds_hash = protocol["dataset"]["dataset_sha256"]
    
    if ds_hash != expected_ds_hash:
        print(f"FAIL: Dataset hash mismatch. Expected {expected_ds_hash}, got {ds_hash}")
        sys.exit(1)
        
    # 3. Check Case IDs
    cases = json.loads(ds_raw.decode("utf-8"))
    case_ids = [c["case_id"] for c in cases]
    case_id_hash = hashlib.sha256(",".join(sorted(case_ids)).encode("utf-8")).hexdigest()
    expected_case_id_hash = protocol["dataset"]["case_id_hash"]
    
    if case_id_hash != expected_case_id_hash:
        print(f"FAIL: Case ID hash mismatch. Expected {expected_case_id_hash}, got {case_id_hash}")
        sys.exit(1)
        
    # 4. Check Prompt Source
    prompt_path = protocol["prompt"]["path"]
    if not os.path.exists(prompt_path):
        print(f"FAIL: Prompt file {prompt_path} not found.")
        sys.exit(1)
        
    with open(prompt_path, "rb") as f:
        prompt_raw = f.read()
        
    prompt_hash = hashlib.sha256(prompt_raw).hexdigest()
    expected_prompt_hash = protocol["prompt"]["prompt_sha256"]
    
    if prompt_hash != expected_prompt_hash:
        print(f"FAIL: Prompt hash mismatch. Expected {expected_prompt_hash}, got {prompt_hash}")
        sys.exit(1)
        
    # 5. Check Output Directory Logic
    out_dir = protocol["output_directory"]
    if not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
        
    print("PASS: Protocol validation successful.")
    print(f"Dataset Hash: {ds_hash}")
    print(f"Case ID Hash: {case_id_hash}")
    print(f"Prompt Hash: {prompt_hash}")
    
if __name__ == "__main__":
    main()
