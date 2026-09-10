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
    
    reasons = {
        "42652369": "The document concerns Google Trends/liver health and does not provide evidence about metformin's inhibition of hepatic gluconeogenesis.",
        "42638417": "The document concerns acetaminophen-induced acute liver injury and does not provide evidence about metformin's inhibition of hepatic gluconeogenesis.",
        "42631638": "The document concerns acetaminophen-induced acute liver injury and does not provide evidence about metformin's inhibition of hepatic gluconeogenesis.",
        "42595240": "The document concerns xenobiotic-induced liver injury and does not provide evidence about metformin's inhibition of hepatic gluconeogenesis."
    }
    
    # Update decisions
    with open(in_csv, newline='', encoding='utf-8') as fin, \
         open(temp_csv, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] == "v3.1h-001" and row["document_id"] in reasons:
                row["human_final_label"] = "NOT_RELEVANT"
                row["human_evidence_span"] = ""
                row["human_annotation_reason"] = reasons[row["document_id"]]
                row["human_confidence"] = "HIGH"
                row["human_agreement"] = "DISAGREE"
                row["human_annotator_id"] = reviewer
                row["human_review_timestamp"] = timestamp
            writer.writerow(row)
            
    temp_csv.replace(in_csv)
    print("Candidates 11-14 successfully recorded.")
    
    # Update progress
    with open(prog_csv, newline='', encoding='utf-8') as fin, \
         open(temp_prog, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] == "v3.1h-001":
                row["candidates_reviewed"] = 14
                row["human_decisions_completed"] = 14
                row["direct_support"] = 1
                row["not_relevant"] = 13
                row["remaining"] = 0
                row["status"] = "CANDIDATE_REVIEW_COMPLETE"
            writer.writerow(row)
            
    temp_prog.replace(prog_csv)
    
    # Document Timestamp Provenance Note
    note_path = Path("reports/audit/v3_1_timestamp_provenance_note.md")
    note = """# Provenance Note on Timestamps
For the AI-assisted human annotation workflow (Phase 2F.2D), the `human_review_timestamp` values recorded in the workspace CSV represent the system-execution time when the Human Decision Helper script recorded the accepted human decision into the file, rather than the exact real-time moment the human reviewer originally conceived the decision. This applies to all automated script insertions during this phase.
"""
    with open(note_path, "w") as f:
        f.write(note)
        
    # Print Case 2 Candidate 1
    with open(in_csv, newline='', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        c_idx = 1
        for row in reader:
            if row["case_id"] == "v3.1h-002":
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