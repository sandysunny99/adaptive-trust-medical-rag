import json
with open("experiments/runs/fusion-evaluation-v3/case_results.jsonl") as f:
    results = [json.loads(l) for l in f]

for r in results:
    if r["f0_first_relevant_rank"] > 5 or r["f3_first_relevant_rank"] > 5:
        print(f"Case: {r['case_id']}")
        print(f"  F0 Rank: {r['f0_first_relevant_rank']}")
        print(f"  F3 Rank: {r['f3_first_relevant_rank']}")
        print(f"  Expected: {r['expected_document_ids']}")
        print(f"  F3 Top N: {r['f3_top_n'][:5]}")