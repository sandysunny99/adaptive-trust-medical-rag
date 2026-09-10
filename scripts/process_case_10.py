import csv
from datetime import datetime, timezone
from pathlib import Path

def main():
    workspace_dir = Path("experiments/annotations/v3_1_human/pilot/reviewer_workspace")
    in_csv = workspace_dir / "decision_helper_review.csv"
    temp_csv = workspace_dir / "decision_helper_review_temp.csv"
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    reviewer = "Reviewer_A"
    
    # Update decision
    with open(in_csv, newline='', encoding='utf-8') as fin, \
         open(temp_csv, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] == "v3.1h-001" and row["document_id"] == "42662744":
                row["human_final_label"] = "NOT_RELEVANT"
                row["human_evidence_span"] = ""
                row["human_annotation_reason"] = "The document concerns doxorubicin delivery to liver cancer cells, but it does not provide evidence about metformin or hepatic gluconeogenesis."
                row["human_confidence"] = "HIGH"
                row["human_agreement"] = "DISAGREE"
                row["human_annotator_id"] = reviewer
                row["human_review_timestamp"] = timestamp
            writer.writerow(row)
            
    temp_csv.replace(in_csv)
    print("Candidate 10 successfully recorded.")
    
    # Count remaining candidates
    remaining = 0
    with open(in_csv, newline='', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        for row in reader:
            if row["case_id"] == "v3.1h-001" and row["human_final_label"] == "":
                remaining += 1
                
    print(f"Remaining candidates for v3.1h-001: {remaining}")

if __name__ == "__main__":
    main()