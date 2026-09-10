import csv
from datetime import datetime, timezone
from pathlib import Path

def main():
    workspace_dir = Path("experiments/annotations/v3_1_human/pilot/reviewer_workspace")
    in_csv = workspace_dir / "decision_helper_review.csv"
    temp_csv = workspace_dir / "decision_helper_review_temp.csv"
    
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    reviewer = "Reviewer_A"
    
    c1_done = False
    c2_done = False
    
    # Update decisions
    with open(in_csv, newline='', encoding='utf-8') as fin, \
         open(temp_csv, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] == "v3.1h-001":
                if row["document_id"] == "41177211":
                    row["human_final_label"] = "DIRECT_SUPPORT"
                    row["human_evidence_span"] = "Metformin decreases hepatic glucose production and decreases intestinal absorption of glucose."
                    row["human_annotation_reason"] = "The source explicitly states that metformin decreases hepatic glucose production, which directly addresses the queried mechanism of inhibition of hepatic gluconeogenesis."
                    row["human_confidence"] = "HIGH"
                    row["human_agreement"] = "DISAGREE"
                    row["human_annotator_id"] = reviewer
                    row["human_review_timestamp"] = timestamp
                    c1_done = True
                elif row["document_id"] == "42661734":
                    row["human_final_label"] = "NOT_RELEVANT"
                    row["human_evidence_span"] = ""
                    row["human_annotation_reason"] = "The available source contains only the title, and the title concerns AMPK activators generally. It does not provide evidence that this document explains how metformin inhibits hepatic gluconeogenesis."
                    row["human_confidence"] = "HIGH"
                    row["human_agreement"] = "DISAGREE" # AI suggested INSUFFICIENT
                    row["human_annotator_id"] = reviewer
                    row["human_review_timestamp"] = timestamp
                    c2_done = True
            writer.writerow(row)
            
    # Replace file
    temp_csv.replace(in_csv)
    print("Candidates 1 and 2 successfully recorded.")
    
    # Print next candidates
    with open(in_csv, newline='', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        c_idx = 1
        for row in reader:
            if row["case_id"] == "v3.1h-001":
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