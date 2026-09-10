import json
import numpy as np
from scipy.stats import wilcoxon, binomtest
from pathlib import Path

out_dir = Path("experiments/runs/fusion-evaluation-v3-real")
with open(out_dir / "case_results.jsonl") as f:
    results = [json.loads(l) for l in f]
    
n_cases = len(results)

# Metrics
pool_recall = sum(1 for r in results if r["f0_first_relevant_rank"] <= 20) / n_cases

f0_r5 = [1 if r["f0_first_relevant_rank"] <= 5 else 0 for r in results]
f3_r5 = [1 if r["f3_first_relevant_rank"] <= 5 else 0 for r in results]

# User rule: MRR should be MRR@20 since we evaluate Top-20
f0_mrr = [1.0/r["f0_first_relevant_rank"] if r["f0_first_relevant_rank"] <= 20 else 0 for r in results]
f3_mrr = [1.0/r["f3_first_relevant_rank"] if r["f3_first_relevant_rank"] <= 20 else 0 for r in results]

# Binary nDCG@5 (IDCG = 1)
f0_ndcg = [1.0/np.log2(r["f0_first_relevant_rank"] + 1) if r["f0_first_relevant_rank"] <= 5 else 0 for r in results]
f3_ndcg = [1.0/np.log2(r["f3_first_relevant_rank"] + 1) if r["f3_first_relevant_rank"] <= 5 else 0 for r in results]

f0_r5_mean = np.mean(f0_r5)
f3_r5_mean = np.mean(f3_r5)
f0_mrr_mean = np.mean(f0_mrr)
f3_mrr_mean = np.mean(f3_mrr)
f0_ndcg_mean = np.mean(f0_ndcg)
f3_ndcg_mean = np.mean(f3_ndcg)

# Paired stats
b = sum(1 for f0, f3 in zip(f0_r5, f3_r5) if f0 == 1 and f3 == 0) # regressed
c = sum(1 for f0, f3 in zip(f0_r5, f3_r5) if f0 == 0 and f3 == 1) # recovered

p_recall = binomtest(c, b + c, 0.5).pvalue if b + c > 0 else 1.0

diff_mrr = np.array(f3_mrr) - np.array(f0_mrr)
p_mrr = wilcoxon(diff_mrr).pvalue if not np.all(diff_mrr == 0) else 1.0

diff_ndcg = np.array(f3_ndcg) - np.array(f0_ndcg)
p_ndcg = wilcoxon(diff_ndcg).pvalue if not np.all(diff_ndcg == 0) else 1.0

recovered = sum(1 for r in results if r["f0_first_relevant_rank"] > 5 and r["f3_first_relevant_rank"] <= 5)
regressed = sum(1 for r in results if r["f0_first_relevant_rank"] <= 5 and r["f3_first_relevant_rank"] > 5)
unchanged = n_cases - (recovered + regressed)

pool_lat = np.mean([r["latency_ms"]["pool_generation"] for r in results])
ce_lat = np.mean([r["latency_ms"]["reranker"] for r in results])
tot_lat = np.mean([r["latency_ms"]["total"] for r in results])

stats = {
    "Candidate_Pool_Recall@20": pool_recall,
    "Delta_Recall@5": f3_r5_mean - f0_r5_mean,
    "Delta_MRR": f3_mrr_mean - f0_mrr_mean,
    "Delta_nDCG@5": f3_ndcg_mean - f0_ndcg_mean,
    "F0": {
        "Recall@5": f0_r5_mean,
        "MRR": f0_mrr_mean,
        "nDCG@5": f0_ndcg_mean
    },
    "F3": {
        "Recall@5": f3_r5_mean,
        "MRR": f3_mrr_mean,
        "nDCG@5": f3_ndcg_mean
    },
    "p_values": {
        "Recall@5_McNemar": p_recall,
        "MRR_Wilcoxon": p_mrr,
        "nDCG@5_Wilcoxon": p_ndcg
    },
    "Rank_Changes": {
        "Recovered": recovered,
        "Regressed": regressed,
        "Unchanged": unchanged
    },
    "Latency_ms": {"pool": pool_lat, "reranker": ce_lat, "total": tot_lat}
}

with open(out_dir / "statistics.json", "w") as f:
    json.dump(stats, f, indent=2)
    
print("V3 Real Stats calculated:")
print(json.dumps(stats, indent=2))