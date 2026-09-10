import csv
from datetime import datetime, timezone
from pathlib import Path

def main():
    workspace_dir = Path("experiments/annotations/v3_1_human/pilot/reviewer_workspace")
    in_csv = workspace_dir / "decision_helper_review.csv"
    temp_csv = workspace_dir / "decision_helper_review_temp.csv"
    prog_csv = workspace_dir / "decision_progress.csv"
    temp_prog = workspace_dir / "decision_progress_temp.csv"
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    reviewer = "Reviewer_A"
    
    decisions = {
        "42679743": ("NOT_RELEVANT", "The document concerns environmental monitoring and a fluorescent probe for liver injury and does not provide evidence about warfarin target INR monitoring.", "HIGH", "DISAGREE"),
        "42246839": ("NOT_RELEVANT", "The document concerns blood monitoring for isotretinoin-treated acne patients and does not provide evidence about warfarin target INR monitoring.", "HIGH", "DISAGREE"),
        "42121128": ("NOT_RELEVANT", "The document concerns therapeutic drug monitoring in a neonatal ICU and does not provide evidence about warfarin target INR monitoring.", "HIGH", "DISAGREE"),
        "42128628": ("NOT_RELEVANT", "The document compares apixaban and rivaroxaban with warfarin in end-stage renal disease but does not address target INR monitoring.", "HIGH", "DISAGREE")
    }
    
    # Update decisions for Case 9 (v3.1h-067)
    with open(in_csv, newline='', encoding='utf-8') as fin, \
         open(temp_csv, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] == "v3.1h-067" and row["document_id"] in decisions:
                label, reason, conf, agree = decisions[row["document_id"]]
                row["human_final_label"] = label
                row["human_evidence_span"] = ""
                row["human_annotation_reason"] = reason
                row["human_confidence"] = conf
                row["human_agreement"] = agree
                row["human_annotator_id"] = reviewer
                row["human_review_timestamp"] = timestamp
            writer.writerow(row)
            
    temp_csv.replace(in_csv)
    print("v3.1h-067 batch decisions successfully recorded.")
    
    # Update progress for Case 9
    with open(prog_csv, newline='', encoding='utf-8') as fin, \
         open(temp_prog, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] == "v3.1h-067":
                row["candidates_reviewed"] = 4
                row["human_decisions_completed"] = 4
                row["not_relevant"] = 4
                row["remaining"] = 0
                row["status"] = "CANDIDATE_REVIEW_COMPLETE"
            writer.writerow(row)
            
    temp_prog.replace(prog_csv)
    print("v3.1h-067 marked as CANDIDATE_REVIEW_COMPLETE.")
    
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    # Print Batch for Case 10 (v3.1h-069)
    case_query = ""
    case_claim = ""
    case_risk = ""
    case_diff = ""
    candidates = []
    
    with open(in_csv, newline='', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        c_idx = 1
        for row in reader:
            if row["case_id"] == "v3.1h-069":
                case_query = row['query']
                case_claim = row['claim_type']
                case_risk = row['risk_tier']
                case_diff = row['difficulty']
                candidates.append({
                    "idx": c_idx,
                    "doc_id": row['document_id'],
                    "title": row['document_title'],
                    "text": row['document_text'],
                    "ai_label": row['ai_suggested_label'],
                    "ai_reason": row['ai_suggested_reason']
                })
                c_idx += 1
                
    print(f"\nCASE ID: v3.1h-069")
    print(f"QUERY: {case_query}")
    print(f"CLAIM TYPE: {case_claim}")
    print(f"RISK TIER: {case_risk}")
    print(f"DIFFICULTY: {case_diff}")
    print("-" * 40)
    for c in candidates:
        print(f"Candidate {c['idx']}")
        print(f"Document ID: {c['doc_id']}")
        print(f"Title: {c['title']}")
        text = c['text']
        print(f"Available source text: {text[:500]}..." if len(text) > 500 else f"Available source text: {text}")
        print(f"AI suggestion: {c['ai_label']}")
        print(f"AI reason: {c['ai_reason']}")
        print("-" * 40)
        

if __name__ == "__main__":
    main()