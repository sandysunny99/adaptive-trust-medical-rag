import json

metrics_r0 = {"recall_at_5": [], "mrr": []}
metrics_r1 = {"recall_at_5": [], "mrr": []}
metrics_r2 = {"recall_at_5": [], "mrr": []}
metrics_r3 = {"recall_at_5": [], "mrr": []}

with open("experiments/runs/retrieval-baseline-v1/case_results.jsonl", "r") as f:
    for line in f:
        r = json.loads(line)
        if r["claim_type"] == "NO_GROUND_TRUTH_EVIDENCE":
            continue
            
        metrics = r["metrics"]
        rec = metrics.get("recall_at_5")
        mrr = metrics.get("mrr")
        
        if rec is not None:
            if r["variant"] == "R0": metrics_r0["recall_at_5"].append(rec)
            if r["variant"] == "R1": metrics_r1["recall_at_5"].append(rec)
            if r["variant"] == "R2": metrics_r2["recall_at_5"].append(rec)
            if r["variant"] == "R3": metrics_r3["recall_at_5"].append(rec)
            
        if mrr is not None:
            if r["variant"] == "R0": metrics_r0["mrr"].append(mrr)
            if r["variant"] == "R1": metrics_r1["mrr"].append(mrr)
            if r["variant"] == "R2": metrics_r2["mrr"].append(mrr)
            if r["variant"] == "R3": metrics_r3["mrr"].append(mrr)

def p(d):
    return {k: sum(v)/len(v) if v else 0.0 for k,v in d.items()}

print("R0:", p(metrics_r0))
print("R1:", p(metrics_r1))
print("R2:", p(metrics_r2))
print("R3:", p(metrics_r3))