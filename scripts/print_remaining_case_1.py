import csv
from pathlib import Path

def main():
    workspace_dir = Path("experiments/annotations/v3_1_human/pilot/reviewer_workspace")
    in_csv = workspace_dir / "decision_helper_review.csv"
    
    print("Remaining Candidates for v3.1h-001:")
    print("-" * 40)
    with open(in_csv, newline='', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        c_idx = 11
        for row in reader:
            if row["case_id"] == "v3.1h-001" and row["human_final_label"] == "":
                print(f"[{c_idx}] CANDIDATE DOCUMENT: {row['document_id']}")
                print(f"TITLE: {row['document_title']}")
                print(f"AI REASON: {row['ai_suggested_reason']}")
                print("-" * 40)
                c_idx += 1

if __name__ == "__main__":
    main()