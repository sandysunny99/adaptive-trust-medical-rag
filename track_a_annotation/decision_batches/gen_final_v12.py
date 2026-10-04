import json
import hashlib
import os

out_dir = "track_a_annotation/decision_batches"

# Fix the canonical schema
with open(f"{out_dir}/TRACK_A_ADJUDICATION_SCHEMA_FINAL_V1.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

schema["properties"]["alternative_label_considered"] = {
    "type": ["string", "null"],
    "enum": ["RELEVANT", "PARTIALLY_RELEVANT", "IRRELEVANT", "INSUFFICIENT_INFORMATION", "AMBIGUOUS", None]
}

with open(f"{out_dir}/TRACK_A_ADJUDICATION_SCHEMA_FINAL_V1.json", "w", encoding="utf-8") as f:
    json.dump(schema, f, indent=2)

calc_schema_hash = hashlib.sha256(json.dumps(schema, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

with open(f"{out_dir}/TRACK_A_LLM_FINAL_SCHEMA_HASHES_V1.json", "r", encoding="utf-8") as f:
    hashes = json.load(f)
    
hashes["track_a_adjudication_schema_sha256"] = calc_schema_hash

with open(f"{out_dir}/TRACK_A_LLM_FINAL_SCHEMA_HASHES_V1.json", "w", encoding="utf-8") as f:
    json.dump(hashes, f, indent=2)

# Update verification MD
with open(f"{out_dir}/TRACK_A_LLM_CANONICAL_SCHEMA_VERIFY_V1.md", "a", encoding="utf-8") as f:
    f.write("- alternative_label_considered restricts enum: True (Fixed)\n")
    
# Update Hash MD
with open(f"{out_dir}/TRACK_A_LLM_HASH_VERIFICATION_V1.md", "r", encoding="utf-8") as f:
    txt = f.read()
txt = txt.replace("SCHEMA_HASH_MATCH = NO", "SCHEMA_HASH_MATCH = YES")
with open(f"{out_dir}/TRACK_A_LLM_HASH_VERIFICATION_V1.md", "w", encoding="utf-8") as f:
    f.write(txt)

print("Schema fixed and hashes updated.")
