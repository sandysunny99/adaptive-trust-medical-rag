import json
from pathlib import Path

def main():
    r1_dir = Path("experiments/runs/retrieval-baseline-phase2c/sapbert/r1")
    r3_dir = Path("experiments/runs/retrieval-baseline-phase2c/sapbert/r3")
    
    with open("experiments/manifests/retrieval_dataset_v2_1.json", "r") as f:
        cases = json.load(f)
        
    for c in cases:
        if not c["expected_document_ids"]: continue
        cid = c["case_id"]
        
        with open(r1_dir / f"{cid}.json") as f: r1 = json.load(f)
        with open(r3_dir / f"{cid}.json") as f: r3 = json.load(f)
        
        if r1["metrics"]["recall_at_5"] == 1.0 and r3["metrics"]["recall_at_5"] == 0.0:
            print(f"Regression in Case {cid}:")
            print(f"  R1 Retrieved: {r1['retrieved_document_ids'][:5]}")
            print(f"  R3 Retrieved: {r3['retrieved_document_ids'][:5]}")
            print(f"  Expected: {c['expected_document_ids']}")

if __name__ == "__main__":
    main()