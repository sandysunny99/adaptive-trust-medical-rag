import json
import numpy as np
from scipy.stats import wilcoxon, binomtest
from pathlib import Path

out_dir = Path("experiments/runs/fusion-evaluation-v3-confirmed")
with open(out_dir / "case_results.jsonl") as f:
    results = [json.loads(l) for l in f]

with open("experiments/manifests/retrieval_ground_truth_v3_confirmed.json") as f:
    gt_docs = {c["case_id"]: c for c in json.load(f)}
    
n_cases = len(results)
positive_cases = len(results)

f0_r1 = np.mean([1.0 if r["f0_first_relevant_rank"] <= 1 else 0 for r in results])
f3_r1 = np.mean([1.0 if r["f3_first_relevant_rank"] <= 1 else 0 for r in results])
f0_r3 = np.mean([1.0 if r["f0_first_relevant_rank"] <= 3 else 0 for r in results])
f3_r3 = np.mean([1.0 if r["f3_first_relevant_rank"] <= 3 else 0 for r in results])
f0_r5 = np.mean([1.0 if r["f0_first_relevant_rank"] <= 5 else 0 for r in results])
f3_r5 = np.mean([1.0 if r["f3_first_relevant_rank"] <= 5 else 0 for r in results])
f0_r10 = np.mean([1.0 if r["f0_first_relevant_rank"] <= 10 else 0 for r in results])
f3_r10 = np.mean([1.0 if r["f3_first_relevant_rank"] <= 10 else 0 for r in results])

f0_mrr = np.mean([r["f0_mrr"] for r in results])
f3_mrr = np.mean([r["f3_mrr"] for r in results])

f0_ndcg = np.mean([1.0/np.log2(r["f0_first_relevant_rank"] + 1) if r["f0_first_relevant_rank"] <= 5 else 0 for r in results])
f3_ndcg = np.mean([1.0/np.log2(r["f3_first_relevant_rank"] + 1) if r["f3_first_relevant_rank"] <= 5 else 0 for r in results])

f0_p5 = np.mean([1.0/5.0 if r["f0_first_relevant_rank"] <= 5 else 0 for r in results])
f3_p5 = np.mean([1.0/5.0 if r["f3_first_relevant_rank"] <= 5 else 0 for r in results])

# Rank changes
b = sum(1 for r in results if r["f0_first_relevant_rank"] <= 5 and r["f3_first_relevant_rank"] > 5) # regressed
c = sum(1 for r in results if r["f0_first_relevant_rank"] > 5 and r["f3_first_relevant_rank"] <= 5) # recovered

p_recall = binomtest(c, b + c, 0.5).pvalue if b + c > 0 else 1.0

diff_mrr = np.array([r["f3_mrr"] for r in results]) - np.array([r["f0_mrr"] for r in results])
p_mrr = wilcoxon(diff_mrr).pvalue if not np.all(diff_mrr == 0) else 1.0

stats = {
    "Candidate_Pool_Recall@20": sum(1 for r in results if r["f0_first_relevant_rank"] <= 20) / positive_cases,
    "Delta_Recall@5": f3_r5 - f0_r5,
    "Delta_MRR": f3_mrr - f0_mrr,
    "Delta_nDCG@5": f3_ndcg - f0_ndcg,
    "F0": {
        "Recall@1": f0_r1,
        "Recall@3": f0_r3,
        "Recall@5": f0_r5,
        "Recall@10": f0_r10,
        "Precision@5": f0_p5,
        "MRR": f0_mrr,
        "nDCG@5": f0_ndcg
    },
    "F3": {
        "Recall@1": f3_r1,
        "Recall@3": f3_r3,
        "Recall@5": f3_r5,
        "Recall@10": f3_r10,
        "Precision@5": f3_p5,
        "MRR": f3_mrr,
        "nDCG@5": f3_ndcg
    },
    "p_values": {
        "Recall@5_McNemar": p_recall,
        "MRR_Wilcoxon": p_mrr
    },
    "Rank_Changes": {
        "Recovered": c,
        "Regressed": b,
        "Unchanged": positive_cases - (c + b)
    }
}

with open(out_dir / "statistics.json", "w") as f:
    json.dump(stats, f, indent=2)
    
print("V3.1 Confirmed Stats calculated:")
print(json.dumps(stats, indent=2))