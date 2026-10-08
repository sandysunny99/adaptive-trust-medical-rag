import json
import os
import csv
from pathlib import Path
from collections import defaultdict
from datetime import datetime

results_file = "experiments/runs/real-llm-v1_2/REAL_LLM_V1_2_RUN_001/results.jsonl"
metrics_file = "experiments/runs/real-llm-v1_2/REAL_LLM_V1_2_RUN_001/metrics.json"
protocol_file = "REAL_LLM_EVALUATION_PROTOCOL_V1_2.json"

with open(results_file, "r", encoding="utf-8") as f:
    records = [json.loads(line) for line in f if line.strip()]

with open(metrics_file, "r", encoding="utf-8") as f:
    metrics = json.load(f)

with open(protocol_file, "r", encoding="utf-8") as f:
    protocol = json.load(f)

# 1. Basic Counts
total_lines = len(records)
valid_json = len(records)
invalid_json = 0
req_ids = [r.get("request_id") for r in records]
unique_req_ids = set(req_ids)
duplicate_req_ids = [r for r in req_ids if req_ids.count(r) > 1]
unique_duplicates = set(duplicate_req_ids)

# 2. Matrix
matrix = defaultdict(list)
for r in records:
    matrix[r.get("case_id")].append(r.get("arm"))

missing_pairs = 0
duplicate_pairs = 0
unexpected_pairs = 0

csv_data = []
for case, arms in matrix.items():
    arm_a_count = arms.count("arm_a")
    arm_b_count = arms.count("arm_b")
    
    if arm_a_count == 0: missing_pairs += 1
    if arm_b_count == 0: missing_pairs += 1
    if arm_a_count > 1: duplicate_pairs += 1
    if arm_b_count > 1: duplicate_pairs += 1
    
    for a in arms:
        if a not in ["arm_a", "arm_b"]: unexpected_pairs += 1
        
    csv_data.append({
        "case_id": case,
        "arm_a_executions": arm_a_count,
        "arm_b_executions": arm_b_count,
        "status": "COMPLETE" if arm_a_count == 1 and arm_b_count == 1 else "ANOMALY"
    })

# 3. Timestamps
starts = [datetime.fromisoformat(r["timestamp_start"]) for r in records]
ends = [datetime.fromisoformat(r["timestamp_end"]) for r in records]

earliest = min(starts) if starts else None
latest = max(ends) if ends else None
duration = (latest - earliest).total_seconds() if earliest and latest else 0

# 4. Consistency
run_ids = set(r.get("run_id") for r in records)
providers = set(r.get("provider") for r in records)
models = set(r.get("model") for r in records)
prompt_hashes = set(r.get("prompt_hash") for r in records)
retrievals = set(r.get("retrieval_identity") for r in records)

prompt_hash_match = "MATCH" if list(prompt_hashes) == ["e5aeb4fa105d30f9df23c6d3815a45d4d63c7e83b82ab30e5fbb9f4721e4301c"] else "FAIL"

# 5. Metric Recomputation
recomputed = {
    "arm_a": {"cases": 0, "claim_support": 0, "citation_val": 0, "unsupported": 0, "abstention": 0, "failures": 0},
    "arm_b": {"cases": 0, "claim_support": 0, "citation_val": 0, "unsupported": 0, "abstention": 0, "failures": 0}
}

malformed = 0

for r in records:
    arm = r.get("arm")
    recomputed[arm]["cases"] += 1
    
    if r.get("status") == "provider_failure":
        recomputed[arm]["failures"] += 1
    elif r.get("status") == "abstained":
        recomputed[arm]["abstention"] += 1
    elif r.get("status") == "SUCCESS":
        m = r.get("metrics", {})
        if m:
            recomputed[arm]["claim_support"] += m.get("claim_support_rate", 0.0)
            recomputed[arm]["citation_val"] += m.get("citation_validation_rate", 0.0)
            recomputed[arm]["unsupported"] += m.get("unsupported_answer_rate", 0.0)
        else:
            malformed += 1
            
# Calculate means
for arm in ["arm_a", "arm_b"]:
    total = recomputed[arm]["cases"]
    if total > 0:
        recomputed[arm]["claim_support_rate"] = recomputed[arm]["claim_support"] / total
        recomputed[arm]["citation_val_rate"] = recomputed[arm]["citation_val"] / total
        recomputed[arm]["unsupported_rate"] = recomputed[arm]["unsupported"] / total
        recomputed[arm]["abstention_rate"] = recomputed[arm]["abstention"] / total
        recomputed[arm]["failure_rate"] = recomputed[arm]["failures"] / total

# Compare with metrics.json
metric_match = "YES"
for arm, m_key in [("arm_a", "arm_a_metrics"), ("arm_b", "arm_b_metrics")]:
    m_json = metrics.get(m_key, {})
    if abs(m_json.get("claim_support", 0) - recomputed[arm]["claim_support_rate"]) > 0.001: metric_match = "NO"
    if abs(m_json.get("citation_val", 0) - recomputed[arm]["citation_val_rate"]) > 0.001: metric_match = "NO"
    if abs(m_json.get("unsupported", 0) - recomputed[arm]["unsupported_rate"]) > 0.001: metric_match = "NO"
    if abs(m_json.get("abstention", 0) - recomputed[arm]["abstention_rate"]) > 0.001: metric_match = "NO"
    if abs(m_json.get("provider_failures", 0) - recomputed[arm]["failure_rate"]) > 0.001: metric_match = "NO"

# Output CSV
with open("V1_2_CASE_ARM_COMPLETION_MATRIX.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["case_id", "arm_a_executions", "arm_b_executions", "status"])
    writer.writeheader()
    for row in csv_data:
        writer.writerow(row)

# Output Metric Recomputation MD
with open("V1_2_METRIC_RECOMPUTATION.md", "w") as f:
    f.write("# V1.2 METRIC RECOMPUTATION\n\n")
    f.write("## RAW RESULT AGGREGATION\n")
    f.write(f"- Arm A Cases: {recomputed['arm_a']['cases']}\n")
    f.write(f"- Arm B Cases: {recomputed['arm_b']['cases']}\n")
    f.write("\n## ARM A RECOMPUTED\n")
    f.write(f"- Claim Support Rate: {recomputed['arm_a']['claim_support_rate']:.4f}\n")
    f.write(f"- Citation Validation Rate: {recomputed['arm_a']['citation_val_rate']:.4f}\n")
    f.write(f"- Unsupported Answer Rate: {recomputed['arm_a']['unsupported_rate']:.4f}\n")
    f.write(f"- Abstention Rate: {recomputed['arm_a']['abstention_rate']:.4f}\n")
    f.write(f"- Provider Failure Rate: {recomputed['arm_a']['failure_rate']:.4f}\n")
    f.write("\n## ARM B RECOMPUTED\n")
    f.write(f"- Claim Support Rate: {recomputed['arm_b']['claim_support_rate']:.4f}\n")
    f.write(f"- Citation Validation Rate: {recomputed['arm_b']['citation_val_rate']:.4f}\n")
    f.write(f"- Unsupported Answer Rate: {recomputed['arm_b']['unsupported_rate']:.4f}\n")
    f.write(f"- Abstention Rate: {recomputed['arm_b']['abstention_rate']:.4f}\n")
    f.write(f"- Provider Failure Rate: {recomputed['arm_b']['failure_rate']:.4f}\n")
    f.write(f"\n## COMPARISON TO metrics.json: {metric_match}\n")

# Output JSON
audit_json = {
    "run_identity": "REAL_LLM_V1_2_RUN_001",
    "protocol_identity": "REAL_LLM_EVALUATION_PROTOCOL_V1_2",
    "total_lines": total_lines,
    "valid_json": valid_json,
    "unique_request_ids": len(unique_req_ids),
    "duplicate_request_ids": len(unique_duplicates),
    "arm_a_count": recomputed["arm_a"]["cases"],
    "arm_b_count": recomputed["arm_b"]["cases"],
    "missing_pairs": missing_pairs,
    "duplicate_pairs": duplicate_pairs,
    "unexpected_pairs": unexpected_pairs,
    "run_ids_consistent": len(run_ids) == 1 and "REAL_LLM_V1_2_RUN_001" in run_ids,
    "provider_consistent": len(providers) == 1 and "Groq" in providers,
    "model_consistent": len(models) == 1 and "openai/gpt-oss-120b" in models,
    "prompt_hash_match": prompt_hash_match == "MATCH",
    "retrieval_consistent": len(retrievals) == 1 and "FROZEN_HISTORICAL_OUTPUT" in retrievals,
    "metric_recomputation_match": metric_match == "YES"
}
with open("V1_2_RUN_FORENSIC_AUDIT.json", "w") as f:
    json.dump(audit_json, f, indent=2)

# Output MD
with open("V1_2_RUN_FORENSIC_AUDIT.md", "w") as f:
    f.write("# V1.2 RUN FORENSIC AUDIT\n\n")
    for k, v in audit_json.items():
        f.write(f"- **{k}**: {v}\n")

print("Generated all audit artifacts.")
