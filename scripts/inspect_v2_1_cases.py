import json

with open("experiments/manifests/retrieval_dataset_v2_1.json", "r") as f:
    cases = json.load(f)

for c in cases:
    if c["expected_document_ids"]:
        print(f"Case {c['case_id']}: {c['claim_type']} | {c['difficulty']} | {c['risk_tier']}")