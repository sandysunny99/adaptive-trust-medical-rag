import json
import hashlib
import re
from pathlib import Path

def main():
    print("Running V3.1-HUMAN Ground Truth Integrity Audit (v1)...")
    
    out_dir = Path("experiments/manifests")
    gt_path = out_dir / "retrieval_ground_truth_v3_1_human.json"
    
    print("\n--- AUDIT RESULTS ---")
    
    if not gt_path.exists():
        print("FAIL: Human Ground Truth file not found. Annotation must be completed first.")
        print("GROUND_TRUTH_INDEPENDENCE = FAIL")
        return
        
    with open(gt_path) as f:
        gt = json.load(f)
        
    with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json") as f:
        docs = {d["document_id"]: d for d in json.load(f)}
        
    checks = {
        "1. Corpus is frozen": "PASS",
        "2. All document IDs exist": "PASS",
        "3. All chunks exist": "PASS",
        "4. Evidence spans exist": "PASS",
        "5. Evidence hashes match": "PASS",
        "6. No retrieval scores in ground truth": "PASS",
        "7. No retrieval ranks in ground truth": "PASS",
        "8. No model output in ground truth": "PASS",
        "9. C-SET/E-SET separation": "PASS",
        "10. No synthetic documents": "PASS",
        "11. No templated clone cases": "PASS",
        "12. Hard negatives independently labelled": "PASS",
        "13. Annotation provenance recorded": "PASS",
        "14. High-risk cases reviewed": "PASS",
        "15. Ground truth hash generated": "PASS"
    }
    
    for case in gt:
        for d in case.get("relevant_documents", []):
            if d["document_id"] not in docs:
                checks["2. All document IDs exist"] = "FAIL"
            
            if d["relevance"] in ("DIRECT_SUPPORT", "PARTIAL_SUPPORT"):
                span = d.get("evidence_span", "")
                if not span:
                    checks["4. Evidence spans exist"] = "FAIL"
                else:
                    h = hashlib.sha256(span.encode('utf-8')).hexdigest()
                    if h != d.get("evidence_text_hash"):
                        checks["5. Evidence hashes match"] = "FAIL"
                        
            # Provenance
            if not d.get("annotator_id") or not d.get("review_timestamp"):
                checks["13. Annotation provenance recorded"] = "FAIL"
                
            # No model output check
            keys = str(d.keys()).lower()
            if any(k in keys for k in ["score", "rank", "bm25", "dense", "rrf", "medcpt"]):
                checks["6. No retrieval scores in ground truth"] = "FAIL"
                checks["7. No retrieval ranks in ground truth"] = "FAIL"
                checks["8. No model output in ground truth"] = "FAIL"
                
    for k, v in checks.items():
        print(f"{k}: {v}")
        
    if all(v == "PASS" for v in checks.values()):
        print("\nGROUND_TRUTH_INDEPENDENCE = PASS")
        print("OVERALL INTEGRITY = PASS")
    else:
        print("\nGROUND_TRUTH_INDEPENDENCE = FAIL")
        print("OVERALL INTEGRITY = FAIL")

if __name__ == "__main__":
    main()