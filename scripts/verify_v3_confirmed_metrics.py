import json
import numpy as np
from pathlib import Path

out_dir = Path("experiments/runs/fusion-evaluation-v3-confirmed")

try:
    with open(out_dir / "case_results.jsonl") as f:
        results = [json.loads(l) for l in f]
except FileNotFoundError:
    print("Run not complete yet, skipping verification.")
    exit(0)
    
with open(out_dir / "statistics.json") as f:
    stats = json.load(f)

print("Verifying V3 Confirmed Metrics independently...")

n_cases = len(results)

# Recalculate
f0_r5 = [1 if r["f0_first_relevant_rank"] <= 5 else 0 for r in results]
f3_r5 = [1 if r["f3_first_relevant_rank"] <= 5 else 0 for r in results]

f0_mrr = [1.0/r["f0_first_relevant_rank"] if r["f0_first_relevant_rank"] <= 20 else 0 for r in results]
f3_mrr = [1.0/r["f3_first_relevant_rank"] if r["f3_first_relevant_rank"] <= 20 else 0 for r in results]

f0_ndcg = [1.0/np.log2(r["f0_first_relevant_rank"] + 1) if r["f0_first_relevant_rank"] <= 5 else 0 for r in results]
f3_ndcg = [1.0/np.log2(r["f3_first_relevant_rank"] + 1) if r["f3_first_relevant_rank"] <= 5 else 0 for r in results]

f0_r5_mean = np.mean(f0_r5)
f3_r5_mean = np.mean(f3_r5)
f0_mrr_mean = np.mean(f0_mrr)
f3_mrr_mean = np.mean(f3_mrr)
f0_ndcg_mean = np.mean(f0_ndcg)
f3_ndcg_mean = np.mean(f3_ndcg)

recovered = sum(1 for r in results if r["f0_first_relevant_rank"] > 5 and r["f3_first_relevant_rank"] <= 5)
regressed = sum(1 for r in results if r["f0_first_relevant_rank"] <= 5 and r["f3_first_relevant_rank"] > 5)

# Verify
assert np.isclose(stats["F0"]["Recall@5"], f0_r5_mean), "F0 Recall mismatch"
assert np.isclose(stats["F3"]["Recall@5"], f3_r5_mean), "F3 Recall mismatch"
assert np.isclose(stats["F0"]["MRR"], f0_mrr_mean), "F0 MRR mismatch"
assert np.isclose(stats["F3"]["MRR"], f3_mrr_mean), "F3 MRR mismatch"
assert np.isclose(stats["F0"]["nDCG@5"], f0_ndcg_mean), "F0 nDCG mismatch"
assert np.isclose(stats["F3"]["nDCG@5"], f3_ndcg_mean), "F3 nDCG mismatch"
assert stats["Rank_Changes"]["Recovered"] == recovered, "Recovery mismatch"
assert stats["Rank_Changes"]["Regressed"] == regressed, "Regression mismatch"

print("All metrics verified independently against case_results.jsonl")