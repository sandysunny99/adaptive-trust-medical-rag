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
    
    # Update decision
    with open(in_csv, newline='', encoding='utf-8') as fin, \
         open(temp_csv, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] == "v3.1h-002" and row["document_id"] == "42654146":
                row["human_final_label"] = "NOT_RELEVANT"
                row["human_evidence_span"] = ""
                row["human_annotation_reason"] = "The document concerns the pharmacokinetics of dabigatran etexilate and the effects of moxifloxacin on intestinal P-glycoprotein, but it does not provide evidence about the clearance pathway of lisinopril."
                row["human_confidence"] = "HIGH"
                row["human_agreement"] = "DISAGREE"
                row["human_annotator_id"] = reviewer
                row["human_review_timestamp"] = timestamp
            writer.writerow(row)
            
    temp_csv.replace(in_csv)
    print("Candidate 9 successfully recorded.")
    
    # Update progress for v3.1h-002
    with open(prog_csv, newline='', encoding='utf-8') as fin, \
         open(temp_prog, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] == "v3.1h-002":
                row["candidates_reviewed"] = 9
                row["human_decisions_completed"] = 9
                row["no_evidence"] = 2
                row["not_relevant"] = 7
                row["remaining"] = 0
                row["status"] = "CANDIDATE_REVIEW_COMPLETE"
            writer.writerow(row)
            
    temp_prog.replace(prog_csv)
    
    # Print first candidate of v3.1h-021
    with open(in_csv, newline='', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        c_idx = 1
        for row in reader:
            if row["case_id"] == "v3.1h-021":
                if row["human_final_label"] == "":
                    print(f"CASE: {row['case_id']}")
                    print(f"QUERY: {row['query']}")
                    print(f"CLAIM TYPE: {row['claim_type']}")
                    print("-" * 40)
                    print(f"[{c_idx}] CANDIDATE DOCUMENT: {row['document_id']}")
                    print(f"TITLE: {row['document_title']}")
                    text = row['document_text']
                    print(f"TEXT: {text[:500]}..." if len(text) > 500 else f"TEXT: {text}")
                    print(f"--- AI RECOMMENDATION ---")
                    print(f"LABEL: {row['ai_suggested_label']}")
                    print(f"REASON: {row['ai_suggested_reason']}")
                    print("-" * 40)
                    break
                c_idx += 1

if __name__ == "__main__":
    main()