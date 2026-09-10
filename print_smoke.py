from adaptive_trust_medical_rag.evaluation.evaluator import make_smoke_dataset
import json

smoke = make_smoke_dataset()
for c in smoke.cases:
    print(json.dumps({"case_id": c.case_id, "query": c.query, "drugs": c.expected_drugs}))