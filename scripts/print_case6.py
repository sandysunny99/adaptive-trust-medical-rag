import csv
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    in_csv = "experiments/annotations/v3_1_human/pilot/reviewer_workspace/decision_helper_review.csv"
    
    case_query = ""
    case_claim = ""
    case_risk = ""
    case_diff = ""
    candidates = []
    
    with open(in_csv, newline='', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        c_idx = 1
        for row in reader:
            if row["case_id"] == "v3.1h-046":
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
                
    print(f"\nCASE ID: v3.1h-046")
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