import json
import csv
from pathlib import Path

def main():
    print("Preparing V3.1-HUMAN PACKAGE v1...")
    
    with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json") as f:
        docs = json.load(f)
        # Sort documents deterministically
        docs.sort(key=lambda x: x["document_id"])
        
    out_dir = Path("experiments/manifests")
    
    # Load cases generated in v0
    with open(out_dir / "v3_1_human_cases.json") as f:
        cases = json.load(f)
        
    csv_path = out_dir / "v3_1_human_v1_review.csv"
    with open(csv_path, "w", newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # 7. Human Annotation UI / CSV Columns
        writer.writerow([
            "case_id", "query", "claim_type", "risk_tier", "difficulty", 
            "document_id", "chunk_id", "document_title", "document_text", 
            "relevance", "evidence_span", "annotation_reason", "authority_tier", 
            "confidence", "annotator_id", "review_timestamp"
        ])
        
        for c in cases:
            # 3. Present the entire frozen corpus to the reviewer. Ordering should be document_id.
            for doc in docs:
                doc_text = doc.get("text", doc.get("abstract", ""))
                doc_title = doc.get("title", "")
                chunk_id = f"chunk-{doc['document_id']}-001"
                
                # 5. Never Automatically Create NO_EVIDENCE
                # 9. Correct the NO_EVIDENCE Workflow: Use PENDING initially
                writer.writerow([
                    c["case_id"], c["query"], c["claim_type"], c["risk_tier"], c["difficulty"],
                    doc["document_id"], chunk_id, doc_title, doc_text,
                    "PENDING", "", "", doc.get("authority_tier", "PEER_REVIEWED_PUBMED"), 
                    "", "", ""
                ])

    print(f"Created {csv_path.name} with {len(cases) * len(docs)} rows.")
    
    guide_content = """# V3.1-HUMAN Annotation Guide v1

## Objective
Judge whether a document actually supports the clinical information need expressed by the query. Do not judge based solely on shared drug names, keywords, or topical similarity.

## Workflow
1. **Initial State**: All candidate combinations are marked `PENDING`.
2. **Review**: Evaluate the documents for each case. You may use text search to find synonyms/abbreviations.
3. **Relevance Labels**:
   - `DIRECT_SUPPORT`: The document explicitly answers the question.
   - `PARTIAL_SUPPORT`: The document addresses the topic but is incomplete.
   - `NOT_RELEVANT`: The document is topically similar but does not contain the specific evidence requested.
4. **No Evidence Assignment**: Only after reviewing all available candidates, if no document in the reviewed corpus provides sufficient evidence, mark a single row for that case as `NO_EVIDENCE` and leave the rest as `NOT_RELEVANT`.
5. **Evidence Span**: For `DIRECT_SUPPORT` and `PARTIAL_SUPPORT`, provide an exact contiguous evidence span copied exactly from the frozen document. Do not paraphrase.

## Specific Domain Rules
- **DDI**: Require evidence of the actual interaction (e.g., increases exposure, reduces clearance, contraindicated). A document that merely mentions both drugs is `NOT_RELEVANT` unless the query asks only about co-occurrence.
- **ADE**: Require evidence that the document connects the drug to the event.
- **Pharmacology**: Require the precise mechanistic answer (target, clearance, etc). A general article is not automatically relevant.
- **Medication Safety**: Require direct support for the safety issue (dosing, contraindication).

## High-Risk Cases
For R3, HIGH_RISK_SAFETY, major DDI, contraindications, overdose, or severe ADE, require a stronger review standard. At least one direct evidence span must be identified for any positive case.

## Authority
Use actual document metadata. Do not infer authority only from the presence of a journal citation. A PubMed article is not an FDA label.

## Blinding
The reviewer must not see retrieval scores or rankings during annotation. You are judging evidence, not system performance.
"""
    with open(out_dir / "v3_1_human_v1_annotation_guide.md", "w") as f:
        f.write(guide_content)
        
    print("Created v3_1_human_v1_annotation_guide.md")

if __name__ == "__main__":
    main()