import json
import os

files_to_check = [
    "COGNEE_GATE5_FINAL_VERIFICATION_V2_RESULTS.jsonl",
    "COGNEE_GATE5_FINAL_VERIFICATION_V2_RELATIONSHIP_RESULTS.jsonl",
    "COGNEE_GATE5_FINAL_VERIFICATION_V2_INTEGRITY_RESULTS.jsonl",
    "COGNEE_GATE5_FINAL_VERIFICATION_V2_PROMPT_INJECTION_RESULTS.jsonl",
    "COGNEE_GATE5_FINAL_VERIFICATION_V2_PROVENANCE_RESULTS.jsonl",
    "COGNEE_GATE5_FINAL_VERIFICATION_V2_POISONING_RESULTS.jsonl",
    "COGNEE_GATE5_FINAL_VERIFICATION_V2_POSITIVE_CONTROL_RESULTS.jsonl",
    "COGNEE_GATE5_FINAL_VERIFICATION_V2_COGNEE_OFF_RESULTS.jsonl",
    "COGNEE_GATE5_FINAL_VERIFICATION_V2_REPRODUCIBILITY_RESULTS.jsonl",
    "../../data/evidence/COGNEE_GATE5_TRUSTED_SOURCE_MANIFEST_V1.jsonl"
]

validation = {
    "artifact_validation_status": "PASSED",
    "checks": []
}

base_dir = "experiments/track_a_abstract_enriched_reannotation_v1"

for f in files_to_check:
    path = os.path.join(base_dir, f)
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    valid_jsonl = False
    record_count = 0
    
    if exists and size > 0:
        valid_jsonl = True
        try:
            with open(path, 'r', encoding='utf-8') as f_in:
                for line in f_in:
                    json.loads(line)
                    record_count += 1
        except Exception as e:
            valid_jsonl = False
            
    validation["checks"].append({
        "file": f,
        "exists": exists,
        "size_bytes": size,
        "valid_jsonl": valid_jsonl,
        "record_count": record_count
    })
    
    if not (exists and size > 0 and valid_jsonl):
        validation["artifact_validation_status"] = "FAILED"
        
out_path = os.path.join(base_dir, "COGNEE_GATE5_FINAL_VERIFICATION_V2_ARTIFACT_VALIDATION.json")
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(validation, f, indent=2)
    
print("Validation complete.")
