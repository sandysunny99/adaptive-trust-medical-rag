import json
import sys

def main():
    filepath = sys.argv[1] if len(sys.argv) > 1 else "experiments/runs/retrieval-baseline-v1/case_results.jsonl"
    results = {"R0": [], "R1": [], "R2": [], "R3": []}
    with open(filepath, "r") as f:
        for line in f:
            if not line.strip(): continue
            d = json.loads(line)
            # Only count positive cases for recall
            if len(d.get("expected_document_ids", [])) > 0:
                results[d["variant"]].append(d["metrics"])
            
    for v, metrics in results.items():
        if not metrics: continue
        r5 = sum(m.get("recall_at_5", 0) for m in metrics) / len(metrics)
        mrr = sum(m.get("mrr", 0) for m in metrics) / len(metrics)
        print(f"{v}: Recall@5: {r5:.3f} | MRR: {mrr:.3f}")

if __name__ == "__main__":
    main()