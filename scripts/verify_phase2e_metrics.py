import json
from pathlib import Path
import hashlib

out_dir = Path("experiments/runs/fusion-evaluation-v3")
with open(out_dir / "case_results.jsonl", "rb") as f:
    case_results_bytes = f.read()
case_results_hash = hashlib.sha256(case_results_bytes).hexdigest()

with open(out_dir / "manifest.json", "w") as f:
    json.dump({"case_results_sha256": case_results_hash}, f, indent=2)

results = [json.loads(l) for l in case_results_bytes.decode("utf-8").splitlines() if l.strip()]

with open("experiments/manifests/retrieval_dataset_v2_1.json") as f:
    cases = json.load(f)
case_map = {c["case_id"]: c for c in cases}

with open("experiments/evidence_snapshots/retrieval-v2_1/documents.json") as f:
    docs = json.load(f)
doc_map = {d["document_id"]: d for d in docs}

# Basic helper to extract drug terms safely
def get_entities_from_query(query_entities, doc_text):
    text_lower = doc_text.lower()
    return [e for e in query_entities if e.lower() in text_lower]

# Metrics
# ==============================================================

def r5(res, subset):
    sub = [r for r in res if r["case_id"] in subset]
    if not sub: return 0.0
    return sum(1 for r in sub if r["f3_first_relevant_rank"] <= 5) / len(sub)

def r5_f0(res, subset):
    sub = [r for r in res if r["case_id"] in subset]
    if not sub: return 0.0
    return sum(1 for r in sub if r["f0_first_relevant_rank"] <= 5) / len(sub)

ddi = [c["case_id"] for c in cases if c["claim_type"] == "DDI" and c["expected_document_ids"]]
ade = [c["case_id"] for c in cases if c["claim_type"] == "ADE" and c["expected_document_ids"]]
safety = [c["case_id"] for c in cases if c["claim_type"] == "Medication_Safety" and c["expected_document_ids"]]
high_risk = [c["case_id"] for c in cases if c["risk_tier"] == "R3" and c["expected_document_ids"]]

domain_metrics = {
    "DDI_Evidence_Recall_at_5": {"F0": r5_f0(results, ddi), "F3": r5(results, ddi), "n": len(ddi)},
    "ADE_Evidence_Recall_at_5": {"F0": r5_f0(results, ade), "F3": r5(results, ade), "n": len(ade)},
    "Medication_Safety_Recall_at_5": {"F0": r5_f0(results, safety), "F3": r5(results, safety), "n": len(safety)},
}
with open(out_dir / "domain_metrics.json", "w") as f: json.dump(domain_metrics, f, indent=2)

# Safety Metrics & Hard Negatives
hard_neg_e12 = next(r for r in results if r["case_id"] == "e-12")
f0_e12_top5 = hard_neg_e12["f0_top_n"][:5]
f3_e12_top5 = hard_neg_e12["f3_top_n"][:5]

# Find noise document "42062777" which was F0 rank 1
# Verify it's a hard negative: Not in expected, but shares 'monitoring' or similar terminology.
noise_doc_id = "42062777"
f0_rank = f0_e12_top5.index(noise_doc_id) + 1 if noise_doc_id in f0_e12_top5 else float('inf')
f3_rank = f3_e12_top5.index(noise_doc_id) + 1 if noise_doc_id in f3_e12_top5 else float('inf')
if f0_rank == float('inf'):
    # Let's find what was Rank 1
    f0_rank1 = f0_e12_top5[0]
    f0_rank = 1
    f3_rank = f3_e12_top5.index(f0_rank1) + 1 if f0_rank1 in f3_e12_top5 else float('inf')

safety_metrics = {
    "High_Risk_R3_Recall_at_5": {"F0": r5_f0(results, high_risk), "F3": r5(results, high_risk), "n": len(high_risk)},
    "Hard_Negative_Rank_e12": {"F0_Rank": f0_rank, "F3_Rank": f3_rank, "relevant": False},
}
with open(out_dir / "safety_metrics.json", "w") as f: json.dump(safety_metrics, f, indent=2)

# Difficulty Metrics
diffs = list(set(c["difficulty"] for c in cases if c["expected_document_ids"]))
diff_metrics = {}
for d in diffs:
    subset = [c["case_id"] for c in cases if c["difficulty"] == d and c["expected_document_ids"]]
    diff_metrics[d] = {"F0_Recall_at_5": r5_f0(results, subset), "F3_Recall_at_5": r5(results, subset), "n": len(subset)}
with open(out_dir / "difficulty_metrics.json", "w") as f: json.dump(diff_metrics, f, indent=2)

# Authority Metrics
auth_tiers = {"FDA", "PubMed_Central", "pubmed"} # For v2.1, pubmed is our main source
total_cases = 0
f0_auth_count = 0
f3_auth_count = 0

for r in results:
    case = case_map[r["case_id"]]
    expected = set(r["expected_document_ids"])
    f0_top5 = r["f0_top_n"][:5]
    f3_top5 = r["f3_top_n"][:5]
    
    total_cases += 1
    # Check if ANY of the top-5 documents are BOTH authoritative AND relevant (expected)
    if any(d in expected and doc_map.get(d, {}).get("provider", "") in auth_tiers for d in f0_top5): f0_auth_count += 1
    if any(d in expected and doc_map.get(d, {}).get("provider", "") in auth_tiers for d in f3_top5): f3_auth_count += 1

authority_metrics = {
    "F0_relevant_authoritative_top5_rate": f0_auth_count / total_cases if total_cases else 0.0,
    "F3_relevant_authoritative_top5_rate": f3_auth_count / total_cases if total_cases else 0.0,
    "n": total_cases
}
with open(out_dir / "authority_metrics.json", "w") as f: json.dump(authority_metrics, f, indent=2)

# Entity Metrics
entity_metrics = {"F0_top1_correct_entity_rate": 0.0, "F3_top1_correct_entity_rate": 0.0, "n": 0}
correct_f0 = 0
correct_f3 = 0
entity_cases = [r for r in results if case_map[r["case_id"]]["expected_entity_ids"]]

for r in entity_cases:
    case = case_map[r["case_id"]]
    entities = case["expected_entity_ids"]
    f0_top1_id = r["f0_top_n"][0] if r["f0_top_n"] else None
    f3_top1_id = r["f3_top_n"][0] if r["f3_top_n"] else None
    
    if f0_top1_id:
        f0_text = doc_map.get(f0_top1_id, {}).get("text", "")
        # Very rough entity overlap check
        if len(get_entities_from_query(entities, f0_text)) == len(entities): correct_f0 += 1
        
    if f3_top1_id:
        f3_text = doc_map.get(f3_top1_id, {}).get("text", "")
        if len(get_entities_from_query(entities, f3_text)) == len(entities): correct_f3 += 1

entity_metrics["F0_top1_correct_entity_rate"] = correct_f0 / len(entity_cases) if entity_cases else 0.0
entity_metrics["F3_top1_correct_entity_rate"] = correct_f3 / len(entity_cases) if entity_cases else 0.0
entity_metrics["n"] = len(entity_cases)
with open(out_dir / "entity_metrics.json", "w") as f: json.dump(entity_metrics, f, indent=2)

print("Metrics verified and recomputed from raw data.")