import csv
from pathlib import Path

def main():
    print("Preparing Human Verification Worksheet...")
    
    in_csv = Path("experiments/annotations/v3_1_human/ai_diagnostic/ai_pilot_review.csv")
    
    verif_dir = Path("experiments/annotations/v3_1_human/pilot/human_verification")
    verif_dir.mkdir(parents=True, exist_ok=True)
    out_csv = verif_dir / "reviewer_A_verification.csv"
    
    required_fields = [
        "case_id", "query", "claim_type", "risk_tier", "difficulty",
        "document_id", "chunk_id", "document_title", "document_text",
        "ai_suggested_label", "ai_suggested_evidence", "ai_suggested_reason",
        "human_final_label", "human_evidence_span", "human_annotation_reason",
        "human_confidence", "human_agreement", "human_annotator_id", "human_review_timestamp"
    ]
    
    with open(in_csv, newline='', encoding='utf-8') as fin, \
         open(out_csv, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=required_fields)
        writer.writeheader()
        
        for row in reader:
            new_row = {
                "case_id": row["case_id"],
                "query": row["query"],
                "claim_type": row["claim_type"],
                "risk_tier": row["risk_tier"],
                "difficulty": row["difficulty"],
                "document_id": row["document_id"],
                "chunk_id": row["chunk_id"],
                "document_title": row["document_title"],
                "document_text": row["document_text"],
                "ai_suggested_label": row["relevance"],
                "ai_suggested_evidence": row["evidence_span"],
                "ai_suggested_reason": row["annotation_reason"],
                "human_final_label": "",
                "human_evidence_span": "",
                "human_annotation_reason": "",
                "human_confidence": "",
                "human_agreement": "",
                "human_annotator_id": "",
                "human_review_timestamp": ""
            }
            writer.writerow(new_row)
            
    print(f"Created verification worksheet: {out_csv}")

if __name__ == "__main__":
    main()