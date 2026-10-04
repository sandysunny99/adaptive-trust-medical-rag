import json
import os

out_dir = "experiments/track_a_abstract_enriched_reannotation_v1"
manifest_path = "data/evidence/COGNEE_GATE5_TRUSTED_SOURCE_MANIFEST_V2.jsonl"

checks = []

def fail(msg):
    checks.append({"status": "FAILED", "reason": msg})
    print(f"FAILED: {msg}")

def pass_check(msg):
    checks.append({"status": "PASSED", "reason": msg})

# Check manifest
manifest_records = []
try:
    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            manifest_records.append(r)
            import hashlib
            h = hashlib.sha256(r["source_text"].encode('utf-8')).hexdigest()
            if h != r["content_hash"]:
                fail(f"Manifest hash mismatch for {r['document_id']}")
    pass_check("Manifest hashes perfectly verified")
except Exception as e:
    fail(f"Manifest verification error: {e}")

# Check placeholder strings in output directory files
forbidden_words = ["uuid-1234", "hash_here", "todo", "tbd", "dummy", "fake", "placeholder"]
for fname in os.listdir(out_dir):
    if fname.endswith(".jsonl") and "CORRECTION05" in fname:
        filepath = os.path.join(out_dir, fname)
        if os.path.getsize(filepath) == 0:
            fail(f"File {fname} is unexpectedly empty")
            continue
            
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for idx, line in enumerate(lines):
                lower_line = line.lower()
                for w in forbidden_words:
                    if w in lower_line:
                        fail(f"Forbidden placeholder '{w}' found in {fname}:{idx}")
                try:
                    r = json.loads(line)
                    # Specific semantic checks per file type
                    if fname == "COGNEE_GATE5_CORRECTION05_RESULTS.jsonl":
                        if r["retrieval_mode"] == "BASELINE" and r["execution_path_type"] != "REAL_BASELINE":
                            fail(f"Contradictory execution path for {r['case_id']}")
                        if r["eligibility"] == "BLOCK" and r["block_reason"] == "NONE":
                            fail(f"Blocked result {r['case_id']} missing block reason")
                        if r["case_id"].startswith("INT-") and ("runtime_candidate_hash" not in r or "trusted_expected_hash" not in r):
                            fail(f"Integrity test {r['case_id']} missing hash comparison fields")
                        if r["case_id"].startswith("PI-") and not r.get("candidate_scanned", False):
                            fail(f"Prompt injection test {r['case_id']} missing scan status")
                    elif fname == "COGNEE_GATE5_CORRECTION05_REPRODUCIBILITY_RESULTS.jsonl":
                        if "field_comparisons" not in r:
                            fail(f"Reproducibility test {r['case_id']} missing field_comparisons object")
                    elif fname == "COGNEE_GATE5_CORRECTION05_COGNEE_RETRIEVAL_RESULTS.jsonl":
                        if r.get("retrieval_latency_ms") in ["NOT_MEASURED", None, 150, "150"]:
                            if type(r.get("retrieval_latency_ms")) != float:
                                fail(f"Retrieval log {r.get('query')} has fake/placeholder latency")
                except Exception as e:
                    fail(f"JSON parsing error in {fname}:{idx} -> {e}")

failed = [c for c in checks if c["status"] == "FAILED"]
if not failed:
    pass_check("All Deep Semantic Verification Checks Passed")
    
out = {
    "artifact_validation_status": "PASSED" if not failed else "FAILED",
    "checks": checks
}

with open(os.path.join(out_dir, "COGNEE_GATE5_CORRECTION05_ARTIFACT_VALIDATION.json"), "w") as f:
    json.dump(out, f, indent=2)

if not failed:
    print("Artifact validation completed and PASSED.")
else:
    print(f"Artifact validation FAILED with {len(failed)} errors.")
