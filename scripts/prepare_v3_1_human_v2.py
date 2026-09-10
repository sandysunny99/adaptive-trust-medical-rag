import json
import csv
from pathlib import Path

def validate_case(c):
    errors = []
    if not c.get("query"): errors.append("empty query")
    if c.get("claim_type") not in ["Pharmacology", "DDI", "ADE", "Medication_Safety"]: errors.append("invalid claim type")
    if c.get("risk_tier") not in ["R0", "R1", "R2", "R3"]: errors.append("invalid risk tier")
    if c.get("difficulty") not in ["EASY_EXACT", "LEXICAL_VARIANT", "SYNONYM", "PARAPHRASE", "MULTI_ENTITY", "MECHANISM", "CYP_DDI", "HIGH_RISK_SAFETY"]: errors.append("invalid difficulty")
    if not c.get("expected_entities"): errors.append("missing entity")
    return errors

def main():
    print("Preparing V3.1-HUMAN PACKAGE v2...")
    
    with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json") as f:
        docs = json.load(f)
        docs.sort(key=lambda x: x["document_id"])
        
    out_dir = Path("experiments/annotations/v3_1_human")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "raw").mkdir(exist_ok=True)
    (out_dir / "completed").mkdir(exist_ok=True)
    
    with open("experiments/manifests/v3_1_human_cases.json") as f:
        cases = json.load(f)
        
    # Validate cases
    print("Validating 80 cases...")
    for c in cases:
        errs = validate_case(c)
        if errs:
            print(f"FAIL Case {c['case_id']}: {errs}")
            return
            
    print("Cases validated successfully. Generating full corpus review CSV...")
    
    csv_path = out_dir / "review.csv"
    with open(csv_path, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            "case_id", "query", "claim_type", "risk_tier", "difficulty", 
            "document_id", "chunk_id", "document_title", "document_text", 
            "relevance", "evidence_span", "annotation_reason", "authority_tier", 
            "confidence", "annotator_id", "review_timestamp"
        ])
        
        for c in cases:
            for doc in docs:
                doc_text = doc.get("text", doc.get("abstract", ""))
                doc_title = doc.get("title", "")
                chunk_id = f"chunk-{doc['document_id']}-001"
                
                writer.writerow([
                    c["case_id"], c["query"], c["claim_type"], c["risk_tier"], c["difficulty"],
                    doc["document_id"], chunk_id, doc_title, doc_text,
                    "PENDING", "", "", doc.get("authority_tier", "PEER_REVIEWED_PUBMED"), 
                    "", "", ""
                ])

    # Verify every row is PENDING
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            assert row["relevance"] == "PENDING"
            count += 1
    
    assert count == len(cases) * len(docs)
    print(f"Created {csv_path.name} with {count} PENDING rows.")
    
    guide_content = """# V3.1-HUMAN Annotation Guide v2

## Objective
Judge whether a document actually supports the clinical information need expressed by the query. Do not judge based solely on shared drug names, keywords, or topical similarity.

## Workflow
1. **Initial State**: All candidate combinations are marked `PENDING`.
2. **Review**: Evaluate the documents for each case. You may use text search to find synonyms/abbreviations. Do not reject a document merely because it uses clinically equivalent terminology.
3. **Relevance Labels**:
   - `DIRECT_SUPPORT`: The document explicitly answers the question.
   - `PARTIAL_SUPPORT`: The document addresses the topic but is incomplete.
   - `NOT_RELEVANT`: The document is topically similar but does not contain the specific evidence requested.
4. **No Evidence Assignment**: Only after reviewing all available candidates, if no document in the reviewed corpus provides sufficient evidence, mark a single row for that case as `NO_EVIDENCE` and leave the rest as `NOT_RELEVANT` or `PENDING`.
5. **Evidence Span**: For `DIRECT_SUPPORT` and `PARTIAL_SUPPORT`, provide an exact contiguous evidence span copied exactly from the frozen document. Do not paraphrase.

## Specific Domain Rules
- **DDI**: Require evidence of the actual interaction (e.g., increases exposure, reduces clearance, contraindicated). A document that merely mentions both drugs is `NOT_RELEVANT`. Note directionality: if A affects B, do not assume B affects A.
- **ADE**: Require evidence that the document connects the drug to the event (e.g., causes, associated with). Recognize negation ("does not increase bleeding", "no association").
- **Pharmacology**: Require the precise mechanistic answer (target, clearance, etc).
- **Medication Safety**: Require direct support for the safety issue (dosing, contraindication).

## High-Risk Cases
For R3 cases (major DDI, contraindications, overdose, severe ADE), require a stronger review standard. At least one direct evidence span must be identified for any positive case.

## Authority
Use actual document metadata. A PubMed article is `PEER_REVIEWED_PUBMED`, not an `FDA_LABEL`.

## Blinding
You are judging evidence, not system performance. You will not see retrieval scores or rankings during annotation.
"""
    with open(out_dir / "annotation_guide.md", "w") as f:
        f.write(guide_content)
        
    readme_content = """# V3.1-HUMAN Annotation Workspace

Welcome to the V3.1-HUMAN Annotation task.

## Instructions
1. Read the `annotation_guide.md` before starting.
2. Open `review.csv`. There are 19,840 review combinations (80 cases x 248 documents).
3. For each case, identify any documents that provide `DIRECT_SUPPORT` or `PARTIAL_SUPPORT`.
4. Update the `relevance` column from `PENDING` to your chosen label.
5. Provide the exact `evidence_span` from the document text.
6. Fill in `annotator_id`, `confidence`, `review_timestamp`, and `annotation_reason`.
7. Once complete, DO NOT overwrite the blank template here. Save your finished work in `completed/review_annotator_id.csv`.

Thank you for contributing to the independent validation of the Medical RAG system.
"""
    with open(out_dir / "README.md", "w") as f:
        f.write(readme_content)
        
    print("Created annotation_guide.md and README.md.")
    
if __name__ == "__main__":
    main()