import csv
from pathlib import Path

def main():
    workspace_dir = Path("experiments/annotations/v3_1_human/pilot/reviewer_workspace")
    in_csv = workspace_dir / "decision_helper_review.csv"
    
    with open(in_csv, newline='', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        count = 0
        for row in reader:
            if row["case_id"] == "v3.1h-001":
                print(f"[{count+1}] CANDIDATE DOCUMENT: {row['document_id']}")
                print(f"TITLE: {row['document_title']}")
                print(f"TEXT: {row['document_text'][:500]}..." if len(row['document_text']) > 500 else f"TEXT: {row['document_text']}")
                print(f"--- AI RECOMMENDATION ---")
                print(f"LABEL: {row['ai_suggested_label']}")
                print(f"EVIDENCE: {row['ai_suggested_evidence']}")
                print(f"REASON: {row['ai_suggested_reason']}")
                print(f"CONFIDENCE: {row['ai_suggested_confidence']}")
                print("-" * 40)
                count += 1
                if count >= 3:
                    break

if __name__ == "__main__":
    main()