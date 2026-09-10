import json
import csv
import hashlib
from pathlib import Path

def main():
    print("Converting V3.1-HUMAN Pilot Annotations to Ground Truth JSON...")
    
    csv_path = Path("experiments/annotations/v3_1_human/completed/reviewer_A.csv")
    out_json = Path("experiments/manifests/retrieval_ground_truth_v3_1_human.json")
    
    with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json", encoding="utf-8") as f:
        docs = {d["document_id"]: d for d in json.load(f)}
        
    with open("experiments/manifests/v3_1_human_cases.json") as f:
        cases_meta = {c["case_id"]: c for c in json.load(f)}
        
    case_results = {}
    
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["case_id"]
            doc_id = row["document_id"]
            rel = row["relevance"]
            
            # Skip PENDING (we are only doing a 10-case pilot, so 70 cases remain PENDING)
            if rel == "PENDING":
                continue
                
            if rel not in ["DIRECT_SUPPORT", "PARTIAL_SUPPORT", "NOT_RELEVANT", "NO_EVIDENCE"]:
                print(f"FAIL: Invalid relevance {rel} in row {row}")
                return
                
            # Validate IDs
            if doc_id not in docs:
                print(f"FAIL: Unknown document_id {doc_id} in case {cid}")
                return
            
            # We don't have chunk data, but assuming standard format here.
            
            if rel in ["DIRECT_SUPPORT", "PARTIAL_SUPPORT"]:
                if not row["evidence_span"]:
                    print(f"FAIL: Missing evidence span for positive case {cid}, doc {doc_id}")
                    return
                doc_text = docs[doc_id].get("text", docs[doc_id].get("abstract", ""))
                if row["evidence_span"] not in doc_text:
                    print(f"FAIL: Evidence span not found in source text for case {cid}, doc {doc_id}")
                    return
                h = hashlib.sha256(row["evidence_span"].encode('utf-8')).hexdigest()
                row["evidence_text_hash"] = h
                
            if rel != "PENDING":
                if not row["annotator_id"] or not row["review_timestamp"] or not row["confidence"]:
                    print(f"FAIL: Missing provenance data in case {cid}")
                    return
                    
            if cid not in case_results:
                case_results[cid] = {
                    "case_id": cid,
                    "query": cases_meta[cid]["query"],
                    "claim_type": cases_meta[cid]["claim_type"],
                    "risk_tier": cases_meta[cid]["risk_tier"],
                    "difficulty": cases_meta[cid]["difficulty"],
                    "expected_entities": cases_meta[cid]["expected_entities"],
                    "ground_truth_status": "VALID",
                    "relevant_documents": []
                }
                
            if rel == "NO_EVIDENCE":
                case_results[cid]["ground_truth_status"] = "NO_EVIDENCE"
            elif rel in ["DIRECT_SUPPORT", "PARTIAL_SUPPORT"]:
                case_results[cid]["relevant_documents"].append({
                    "document_id": doc_id,
                    "chunk_id": row["chunk_id"],
                    "relevance": rel,
                    "evidence_span": row["evidence_span"],
                    "evidence_text_hash": row["evidence_text_hash"],
                    "annotation_reason": row["annotation_reason"],
                    "authority_tier": row["authority_tier"],
                    "confidence": row["confidence"],
                    "annotator_id": row["annotator_id"],
                    "review_timestamp": row["review_timestamp"]
                })
                
    out_list = list(case_results.values())
    if len(out_list) != 10:
        print(f"Expected 10 pilot cases, got {len(out_list)}.")
        return
        
    with open(out_json, "w") as f:
        json.dump(out_list, f, indent=2)
        
    print(f"Successfully converted {len(out_list)} cases to Ground Truth JSON.")

if __name__ == "__main__":
    main()