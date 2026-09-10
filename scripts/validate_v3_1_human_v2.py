import json
import hashlib
import csv
import re
from pathlib import Path

def normalize(q):
    return re.sub(r'[^a-z0-9]', ' ', q.lower()).strip()

c_set = [
    "metformin pharmacology",
    "warfarin aspirin interaction",
    "CYP2C9 drug interactions",
    "drug induced liver injury",
    "spironolactone hyperkalemia",
    "atorvastatin mechanism of action",
    "lisinopril renal clearance",
    "omeprazole clopidogrel interaction",
    "levothyroxine iron interaction",
    "citalopram qt prolongation",
    "doxorubicin cardiotoxicity",
    "amiodarone pulmonary toxicity",
    "isotretinoin teratogenicity",
    "acetaminophen hepatotoxicity",
    "digoxin toxicity monitoring",
    "alendronate esophageal ulcer",
    "pantoprazole clopidogrel",
    "fluoxetine cyp2d6",
    "sertraline pregnancy",
    "gabapentin sedation",
    "tramadol seizure risk",
    "celecoxib cardiovascular risk",
    "rivaroxaban bleeding antidote",
    "apixaban renal dosing",
    "dabigatran reversal agent"
]

def check_query_independence(cases):
    c_norms = set(normalize(c) for c in c_set)
    exact = 0
    high_overlap = 0
    duplicates = 0
    
    seen = set()
    for case in cases:
        q = case["query"]
        q_norm = normalize(q)
        
        # Check clones
        if q_norm in seen:
            duplicates += 1
        seen.add(q_norm)
        
        # Check C-SET
        if q_norm in c_norms:
            exact += 1
            
        q_tok = set(q_norm.split())
        for c_norm in c_norms:
            c_tok = set(c_norm.split())
            if not q_tok or not c_tok: continue
            overlap = len(q_tok & c_tok) / max(len(q_tok), len(c_tok))
            if overlap > 0.8:
                high_overlap += 1
                
    return exact == 0 and high_overlap == 0 and duplicates == 0, exact, high_overlap, duplicates

def main():
    print("Running V3.1-HUMAN Ground Truth Integrity Audit (v2)...")
    
    out_dir = Path("experiments/annotations/v3_1_human")
    manifest_dir = Path("experiments/manifests")
    
    checks = {
        "1. Corpus frozen": "NOT_CHECKED",
        "2. Document IDs valid": "NOT_CHECKED",
        "3. Chunk IDs valid": "NOT_CHECKED",
        "4. Evidence spans valid": "NOT_CHECKED",
        "5. Evidence hashes valid": "NOT_CHECKED",
        "6. No retrieval scores in GT": "NOT_CHECKED",
        "7. No retrieval ranks in GT": "NOT_CHECKED",
        "8. No synthetic documents": "NOT_CHECKED",
        "9. No templated clone cases": "NOT_CHECKED",
        "10. C-SET/E-SET separation": "NOT_CHECKED",
        "11. Human annotation provenance": "NOT_CHECKED",
        "12. High-risk review": "NOT_CHECKED",
        "13. Ground truth hash generated": "NOT_CHECKED",
        "14. NO_EVIDENCE correctly used": "NOT_CHECKED",
        "15. All rows present": "NOT_CHECKED"
    }
    
    # 1. Corpus frozen
    corpus_file = Path("experiments/evidence_snapshots/retrieval-v3-real/documents.json")
    if not corpus_file.exists():
        checks["1. Corpus frozen"] = "FAIL"
    else:
        with open(corpus_file) as f:
            docs = json.load(f)
            doc_map = {d["document_id"]: d for d in docs}
        
        with open("experiments/evidence_snapshots/retrieval-v3-real/manifest.json") as f:
            c_manifest = json.load(f)
            
        canonical_docs = json.dumps(docs, sort_keys=True, separators=(",", ":")).encode("utf-8")
        act_hash = hashlib.sha256(canonical_docs).hexdigest()
        if act_hash == c_manifest.get("corpus_sha256"):
            checks["1. Corpus frozen"] = "PASS"
            checks["8. No synthetic documents"] = "PASS" # Same corpus as frozen baseline
        else:
            checks["1. Corpus frozen"] = "FAIL"
            
    # Load Cases
    with open(manifest_dir / "v3_1_human_cases.json") as f:
        cases = json.load(f)
        
    indep, exact, high, dupes = check_query_independence(cases)
    if indep:
        checks["9. No templated clone cases"] = "PASS"
        checks["10. C-SET/E-SET separation"] = "PASS"
    else:
        checks["9. No templated clone cases"] = "FAIL" if dupes > 0 else "PASS"
        checks["10. C-SET/E-SET separation"] = "FAIL"
        print(f"   -> Overlaps found: exact={exact}, high={high}, dupes={dupes}")
        
    # Check Ground Truth
    gt_path = manifest_dir / "retrieval_ground_truth_v3_1_human.json"
    if not gt_path.exists():
        checks["2. Document IDs valid"] = "NOT_APPLICABLE (GT not created)"
        checks["3. Chunk IDs valid"] = "NOT_APPLICABLE (GT not created)"
        checks["4. Evidence spans valid"] = "NOT_APPLICABLE (GT not created)"
        checks["5. Evidence hashes valid"] = "NOT_APPLICABLE (GT not created)"
        checks["6. No retrieval scores in GT"] = "NOT_APPLICABLE (GT not created)"
        checks["7. No retrieval ranks in GT"] = "NOT_APPLICABLE (GT not created)"
        checks["11. Human annotation provenance"] = "NOT_APPLICABLE (GT not created)"
        checks["12. High-risk review"] = "NOT_APPLICABLE (GT not created)"
        checks["13. Ground truth hash generated"] = "NOT_APPLICABLE (GT not created)"
        checks["14. NO_EVIDENCE correctly used"] = "NOT_APPLICABLE (GT not created)"
        checks["15. All rows present"] = "NOT_APPLICABLE (GT not created)"
    else:
        # If the user completed it, we would validate everything here.
        pass
        
    print("\n--- AUDIT RESULTS ---")
    for k, v in checks.items():
        print(f"{k}: {v}")
        
    if all(v == "PASS" for v in checks.values() if "NOT_APPLICABLE" not in v):
        if not gt_path.exists():
            print("\nGROUND_TRUTH_INDEPENDENCE = FAIL (Waiting for human annotation)")
            print("OVERALL INTEGRITY = FAIL")
        else:
            print("\nGROUND_TRUTH_INDEPENDENCE = PASS")
            print("OVERALL INTEGRITY = PASS")
    else:
        print("\nGROUND_TRUTH_INDEPENDENCE = FAIL")
        print("OVERALL INTEGRITY = FAIL")

if __name__ == "__main__":
    main()