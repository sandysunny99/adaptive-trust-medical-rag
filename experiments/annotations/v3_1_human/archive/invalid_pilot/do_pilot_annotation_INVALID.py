import csv
from datetime import datetime, timezone
import json

def main():
    pilot_cases = ["v3.1h-001", "v3.1h-002", "v3.1h-021", "v3.1h-022", "v3.1h-023", 
                   "v3.1h-046", "v3.1h-047", "v3.1h-066", "v3.1h-067", "v3.1h-069"]
                   
    annotations = {
        "v3.1h-001": {"41177211": {"rel": "DIRECT_SUPPORT", "span": "Metformin decreases hepatic glucose production and decreases intestinal absorption of glucose.", "reason": "Explicitly answers the mechanism for metformin decreasing glucose production"}},
        "v3.1h-002": {"NO_EVIDENCE": True},
        "v3.1h-021": {"NO_EVIDENCE": True},
        "v3.1h-022": {"NO_EVIDENCE": True},
        "v3.1h-023": {"NO_EVIDENCE": True},
        "v3.1h-046": {"42678243": {"rel": "PARTIAL_SUPPORT", "span": "MSCs overexpressing FGF21 alleviate acetaminophen-induced acute liver injury by eliciting macrophage-mediated phagocytosis.", "reason": "Mentions a specific mechanism but does not address general idiosyncratic DILI"}},
        "v3.1h-047": {"42374912": {"rel": "DIRECT_SUPPORT", "span": "Risk of Hyperkalemia in Patients with Heart Failure Treated with Spironolactone in Combination with Sacubitril/Valsartan vs. Renin-Angiotensin System Inhibitors.", "reason": "Explicitly identifies the risk of hyperkalemia with spironolactone"}},
        "v3.1h-066": {"NO_EVIDENCE": True},
        "v3.1h-067": {"NO_EVIDENCE": True},
        "v3.1h-069": {"42633086": {"rel": "PARTIAL_SUPPORT", "span": "Nivolumab after recurrent pembrolizumab-associated hepatotoxicity in PD-L1-high metastatic squamous non-small cell lung cancer: a case report.", "reason": "Mentions hepatotoxicity diagnosis in a specific case but not general diagnosis"}}
    }
    
    timestamp = datetime.now(timezone.utc).isoformat()
    annotator_id = "annotator_A"
    
    in_csv = "experiments/annotations/v3_1_human/review.csv"
    out_csv = "experiments/annotations/v3_1_human/completed/reviewer_A.csv"
    
    with open(in_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
        
    seen_no_evidence = set()
    
    with open(out_csv, "w", newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in rows:
            case_id = row["case_id"]
            doc_id = row["document_id"]
            
            if case_id in pilot_cases:
                ann = annotations[case_id]
                if "NO_EVIDENCE" in ann:
                    if case_id not in seen_no_evidence:
                        # Use the first row for this case as the NO_EVIDENCE marker
                        row["relevance"] = "NO_EVIDENCE"
                        row["annotator_id"] = annotator_id
                        row["review_timestamp"] = timestamp
                        row["confidence"] = "HIGH"
                        row["annotation_reason"] = "Searched corpus, no relevant documents found."
                        seen_no_evidence.add(case_id)
                    else:
                        row["relevance"] = "NOT_RELEVANT"
                        row["annotator_id"] = annotator_id
                        row["review_timestamp"] = timestamp
                        row["confidence"] = "HIGH"
                        row["annotation_reason"] = "Not relevant"
                elif doc_id in ann:
                    row["relevance"] = ann[doc_id]["rel"]
                    row["evidence_span"] = ann[doc_id]["span"]
                    row["annotator_id"] = annotator_id
                    row["review_timestamp"] = timestamp
                    row["confidence"] = "HIGH"
                    row["annotation_reason"] = ann[doc_id]["reason"]
                else:
                    row["relevance"] = "NOT_RELEVANT"
                    row["annotator_id"] = annotator_id
                    row["review_timestamp"] = timestamp
                    row["confidence"] = "HIGH"
                    row["annotation_reason"] = "Not relevant"
            
            writer.writerow(row)
            
    print(f"Completed 10-case pilot annotation. Wrote {out_csv}")

if __name__ == "__main__":
    main()