import json
with open("experiments/runs/fusion-evaluation-v3/case_results.jsonl") as f:
    results = [json.loads(l) for l in f]

f0_r5 = sum(1 for r in results if r["f0_first_relevant_rank"] <= 5) / len(results)
f3_r5 = sum(1 for r in results if r["f3_first_relevant_rank"] <= 5) / len(results)

f0_mrr = sum(1.0/r["f0_first_relevant_rank"] if r["f0_first_relevant_rank"] <= 5 else 0 for r in results) / len(results)
f3_mrr = sum(1.0/r["f3_first_relevant_rank"] if r["f3_first_relevant_rank"] <= 5 else 0 for r in results) / len(results)

f3_pool_latency = sum(r["latency_ms"]["pool_generation"] for r in results) / len(results)
f3_ce_latency = sum(r["latency_ms"]["reranker"] for r in results) / len(results)
f3_total_latency = sum(r["latency_ms"]["total"] for r in results) / len(results)

print(f"F0 Recall@5: {f0_r5:.3f} | MRR: {f0_mrr:.3f}")
print(f"F3 Recall@5: {f3_r5:.3f} | MRR: {f3_mrr:.3f}")
print(f"F3 Latency: Pool={f3_pool_latency:.1f}ms, CE={f3_ce_latency:.1f}ms, Total={f3_total_latency:.1f}ms")