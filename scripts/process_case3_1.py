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
            if row["case_id"] == "v3.1h-021" and row["document_id"] == "40825054":
                row["human_final_label"] = "NO_EVIDENCE"
                row["human_evidence_span"] = ""
                row["human_annotation_reason"] = "The document concerns hemorrhagic complications involving alteplase with antiplatelet or anticoagulant therapy, but the available frozen source does not establish a specific warfarin-plus-aspirin bleeding interaction."
                row["human_confidence"] = "LOW"
                row["human_agreement"] = "DISAGREE"
                row["human_annotator_id"] = reviewer
                row["human_review_timestamp"] = timestamp
            writer.writerow(row)
            
    temp_csv.replace(in_csv)
    print("Candidate 1 successfully recorded.")
    
    # Print Candidate 2
    with open(in_csv, newline='', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        c_idx = 1
        for row in reader:
            if row["case_id"] == "v3.1h-021":
                if row["human_final_label"] == "":
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