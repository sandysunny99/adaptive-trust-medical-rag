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
        "32699722": ("NO_EVIDENCE", "The document concerns metformin-associated lactic acidosis and is potentially relevant to metformin safety, but the available frozen source does not establish the contraindication of metformin in severe renal disease.", "LOW", "DISAGREE"),
        "42661734": ("NOT_RELEVANT", "The document concerns resveratrol, metformin, and endothelial dysfunction and does not address renal contraindication or severe renal disease.", "HIGH", "DISAGREE"),
        "41177211": ("NOT_RELEVANT", "The document provides metformin mechanism-of-action evidence about hepatic glucose production but does not address the medication-safety question of contraindication in severe renal disease.", "HIGH", "DISAGREE"),
        "42636576": ("NOT_RELEVANT", "The document concerns statin dosing and cholesterol response and does not address metformin or severe renal disease.", "HIGH", "DISAGREE"),
        "42475421": ("NOT_RELEVANT", "The document concerns kidney function in diabetic mice using a VEGFR1-blocking antibody and does not discuss metformin contraindication.", "HIGH", "DISAGREE"),
        "42438581": ("NOT_RELEVANT", "The document concerns a levothyroxine-iron interaction and does not address metformin or renal contraindication.", "HIGH", "DISAGREE"),
        "41748094": ("NOT_RELEVANT", "The document concerns antidepressant dose changes and cardiac safety and does not address metformin renal contraindication.", "HIGH", "DISAGREE"),
        "42359186": ("NOT_RELEVANT", "The document concerns amiodarone pulmonary toxicity and does not address metformin renal contraindication.", "HIGH", "DISAGREE"),
        "42332214": ("NOT_RELEVANT", "The document concerns amiodarone dosing and pulmonary toxicity and does not address metformin renal contraindication.", "HIGH", "DISAGREE"),
        "42295720": ("NOT_RELEVANT", "The document concerns isotretinoin dosing for acne and does not address metformin renal contraindication.", "HIGH", "DISAGREE"),
        "42663261": ("NOT_RELEVANT", "The document concerns acetaminophen overdose treatment and does not address metformin renal contraindication.", "HIGH", "DISAGREE"),
        "41323006": ("NOT_RELEVANT", "The document concerns analgesic efficacy and safety of ketoprofen, tramadol, and morphine and does not address metformin renal contraindication.", "HIGH", "DISAGREE"),
        "41158891": ("NOT_RELEVANT", "The document concerns tramadol-associated seizures and does not address metformin renal contraindication.", "HIGH", "DISAGREE"),
        "42670022": ("NOT_RELEVANT", "The document concerns apixaban dosing in kidney failure and does not address metformin.", "HIGH", "DISAGREE"),
        "42394350": ("NOT_RELEVANT", "The document concerns direct oral anticoagulant levels in nursing-home residents and does not address metformin renal contraindication.", "HIGH", "DISAGREE")
    }
    
    # Update decisions for Case 8 (v3.1h-066)
    with open(in_csv, newline='', encoding='utf-8') as fin, \
         open(temp_csv, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] == "v3.1h-066" and row["document_id"] in decisions:
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
    print("v3.1h-066 batch decisions successfully recorded.")
    
    # Update progress for Case 8
    with open(prog_csv, newline='', encoding='utf-8') as fin, \
         open(temp_prog, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] == "v3.1h-066":
                row["candidates_reviewed"] = 15
                row["human_decisions_completed"] = 15
                row["no_evidence"] = 1
                row["not_relevant"] = 14
                row["remaining"] = 0
                row["status"] = "CANDIDATE_REVIEW_COMPLETE"
            writer.writerow(row)
            
    temp_prog.replace(prog_csv)
    print("v3.1h-066 marked as CANDIDATE_REVIEW_COMPLETE.")
    
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    # Print Batch for Case 9 (v3.1h-067)
    case_query = ""
    case_claim = ""
    case_risk = ""
    case_diff = ""
    candidates = []
    
    with open(in_csv, newline='', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        c_idx = 1
        for row in reader:
            if row["case_id"] == "v3.1h-067":
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
                
    print(f"\nCASE ID: v3.1h-067")
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