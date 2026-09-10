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
        "42677606": ("NOT_RELEVANT", "The document concerns copper-induced oxidative stress in chicken hepatocytes and does not provide evidence about mechanisms of idiosyncratic drug-induced liver injury.", "HIGH"),
        "42667784": ("NOT_RELEVANT", "The document concerns a decoction for diabetic cataract and does not support the requested idiosyncratic DILI mechanism.", "HIGH"),
        "42661734": ("NOT_RELEVANT", "The document concerns resveratrol, metformin, and endothelial dysfunction and does not address idiosyncratic drug-induced liver injury mechanisms.", "HIGH"),
        "42653808": ("NOT_RELEVANT", "The document concerns berberine-drug interactions and does not address idiosyncratic drug-induced liver injury mechanisms.", "HIGH"),
        "42653173": ("NOT_RELEVANT", "The document concerns analgesic-psychotropic polypharmacy toxicity and does not support the requested idiosyncratic DILI mechanism.", "HIGH"),
        "42677663": ("NOT_RELEVANT", "The document concerns BDE-47 environmental exposure and hepatocyte DNA damage, not idiosyncratic drug-induced liver injury.", "HIGH"),
        "42674049": ("NO_EVIDENCE", "The document addresses drug-induced liver injury and is potentially relevant to the query, but the available frozen source contains only the title and does not establish the mechanisms of idiosyncratic drug-induced liver injury.", "LOW"),
        "42678094": ("NOT_RELEVANT", "The document concerns statin-ezetimibe combination mechanisms and does not address idiosyncratic DILI.", "HIGH"),
        "42681676": ("NOT_RELEVANT", "The document concerns breast cancer stem cells and protein delivery and does not address idiosyncratic DILI mechanisms.", "HIGH"),
        "42670540": ("NOT_RELEVANT", "The document concerns doxorubicin-induced cardiotoxicity and does not address idiosyncratic DILI mechanisms.", "HIGH"),
        "42628776": ("NOT_RELEVANT", "The document concerns acetaminophen-induced acute kidney injury and does not support the requested idiosyncratic DILI mechanism.", "HIGH"),
        "42318218": ("NOT_RELEVANT", "The document concerns proton-pump-inhibitor-induced insulin autoimmune syndrome and does not address idiosyncratic DILI mechanisms.", "HIGH")
    }
    
    # Update decisions for Case 6 (v3.1h-046)
    with open(in_csv, newline='', encoding='utf-8') as fin, \
         open(temp_csv, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] == "v3.1h-046" and row["document_id"] in decisions:
                label, reason, conf = decisions[row["document_id"]]
                row["human_final_label"] = label
                row["human_evidence_span"] = ""
                row["human_annotation_reason"] = reason
                row["human_confidence"] = conf
                row["human_agreement"] = "DISAGREE"
                row["human_annotator_id"] = reviewer
                row["human_review_timestamp"] = timestamp
            writer.writerow(row)
            
    temp_csv.replace(in_csv)
    print("v3.1h-046 batch decisions successfully recorded.")
    
    # Update progress for Case 6
    with open(prog_csv, newline='', encoding='utf-8') as fin, \
         open(temp_prog, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] == "v3.1h-046":
                row["candidates_reviewed"] = 12
                row["human_decisions_completed"] = 12
                row["no_evidence"] = 1
                row["not_relevant"] = 11
                row["remaining"] = 0
                row["status"] = "CANDIDATE_REVIEW_COMPLETE"
            writer.writerow(row)
            
    temp_prog.replace(prog_csv)
    print("v3.1h-046 marked as CANDIDATE_REVIEW_COMPLETE.")
    
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    # Print Batch for Case 7 (v3.1h-047)
    case_query = ""
    case_claim = ""
    case_risk = ""
    case_diff = ""
    candidates = []
    
    with open(in_csv, newline='', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        c_idx = 1
        for row in reader:
            if row["case_id"] == "v3.1h-047":
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
                
    print(f"\nCASE ID: v3.1h-047")
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