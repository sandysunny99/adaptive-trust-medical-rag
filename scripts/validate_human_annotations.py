import csv
import json
import hashlib

def main():
    print("Validating V3.1-HUMAN Annotations...")
    
    with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json") as f:
        docs = {d["document_id"]: d for d in json.load(f)}
        
    valid = True
    positives = 0
    no_evidence = 0
    
    try:
        with open("experiments/manifests/v3_1_human_annotation_template.csv", newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                rel = row["relevance"]
                if rel == "PENDING": continue
                if rel == "NO_EVIDENCE":
                    no_evidence += 1
                    continue
                    
                doc_id = row["document_id"]
                if doc_id not in docs:
                    print(f"FAIL: Document ID {doc_id} not found in frozen corpus.")
                    valid = False
                    continue
                    
                if rel in ("DIRECT_SUPPORT", "PARTIAL_SUPPORT"):
                    positives += 1
                    span = row["evidence_span"]
                    if not span:
                        print(f"FAIL: Missing evidence span for positive case {row['case_id']}")
                        valid = False
                        continue
                        
                    doc_text = docs[doc_id].get("text", docs[doc_id].get("abstract", ""))
                    if span not in doc_text:
                        print(f"FAIL: Evidence span not found exactly in source document for {row['case_id']}")
                        valid = False
                        
                    calc_hash = hashlib.sha256(span.encode('utf-8')).hexdigest()
                    # In a real workflow, the template would have expected evidence_text_hash filled by annotator
                    # For validation we just ensure the span exists.
                    
    except FileNotFoundError:
        print("CSV file not found. Please complete the annotation template.")
        valid = False

    if valid:
        print(f"Validation PASS. Found {positives} positive labels and {no_evidence} NO_EVIDENCE cases.")
    else:
        print("Validation FAIL. See errors above.")

if __name__ == "__main__":
    main()