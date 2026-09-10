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
        "42679743": ("NOT_RELEVANT", "The document concerns liver injury diagnosis and environmental monitoring but does not specifically address diagnosis of drug-induced hepatotoxicity.", "HIGH", "DISAGREE"),
        "42674049": ("NO_EVIDENCE", "The document specifically concerns drug-induced liver injury and is potentially relevant to the query, but the frozen source contains only the title and does not establish diagnostic criteria or a diagnostic method for drug-induced hepatotoxicity.", "LOW", "DISAGREE"),
        "42633086": ("NOT_RELEVANT", "The document concerns pembrolizumab-associated hepatotoxicity in a specific cancer case and does not address the general diagnosis of drug-induced hepatotoxicity.", "HIGH", "DISAGREE")
    }
    
    # Update decisions for Case 10 (v3.1h-069)
    with open(in_csv, newline='', encoding='utf-8') as fin, \
         open(temp_csv, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] == "v3.1h-069" and row["document_id"] in decisions:
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
    print("v3.1h-069 batch decisions successfully recorded.")
    
    # Update progress for Case 10
    with open(prog_csv, newline='', encoding='utf-8') as fin, \
         open(temp_prog, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] == "v3.1h-069":
                row["candidates_reviewed"] = 3
                row["human_decisions_completed"] = 3
                row["no_evidence"] = 1
                row["not_relevant"] = 2
                row["remaining"] = 0
                row["status"] = "CANDIDATE_REVIEW_COMPLETE"
            writer.writerow(row)
            
    temp_prog.replace(prog_csv)
    print("v3.1h-069 marked as CANDIDATE_REVIEW_COMPLETE.")
    

if __name__ == "__main__":
    main()