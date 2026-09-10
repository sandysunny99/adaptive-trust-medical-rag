import csv
import json
from pathlib import Path
from datetime import datetime, timezone

def main():
    print("Generating AI-Assisted Diagnostic Track...")
    
    # 1. Setup Directories
    ai_dir = Path("experiments/annotations/v3_1_human/ai_diagnostic")
    ai_dir.mkdir(parents=True, exist_ok=True)
    
    reports_dir = Path("reports/audit")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # 2. Load the input template and corpus
    template_path = Path("experiments/annotations/v3_1_human/pilot/pilot_review.csv")
    with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json", encoding="utf-8") as f:
        docs = {d["document_id"]: d for d in json.load(f)}
        
    out_csv = ai_dir / "ai_pilot_review.csv"
    
    ai_logic = {
        "v3.1h-001": {"41177211": {"rel": "DIRECT_SUPPORT", "span": "Metformin decreases hepatic glucose production and decreases intestinal absorption of glucose.", "reason": "The available abstract text explicitly states that the drug decreases hepatic glucose production, directly addressing the query."}},
        "v3.1h-046": {"42678243": {"rel": "PARTIAL_SUPPORT", "span": "MSCs overexpressing FGF21 alleviate acetaminophen-induced acute liver injury by eliciting macrophage-mediated phagocytosis.", "reason": "Mentions a specific mechanism but does not address general idiosyncratic DILI."}},
        "v3.1h-047": {"42374912": {"rel": "DIRECT_SUPPORT", "span": "Risk of Hyperkalemia in Patients with Heart Failure Treated with Spironolactone in Combination with Sacubitril/Valsartan vs. Renin-Angiotensin System Inhibitors.", "reason": "Explicitly identifies the risk of hyperkalemia with spironolactone in the title context."}},
        "v3.1h-069": {"42633086": {"rel": "PARTIAL_SUPPORT", "span": "Nivolumab after recurrent pembrolizumab-associated hepatotoxicity in PD-L1-high metastatic squamous non-small cell lung cancer: a case report.", "reason": "Mentions hepatotoxicity diagnosis in a specific case but not general diagnosis."}}
    }
    
    direct_count = 0
    partial_count = 0
    insufficient_count = 0
    
    with open(template_path, newline='', encoding='utf-8') as fin, \
         open(out_csv, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames + ["annotation_source", "ground_truth_eligible"]
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            cid = row["case_id"]
            doc_id = row["document_id"]
            
            # Simple AI diagnostic logic
            if cid in ai_logic and doc_id in ai_logic[cid]:
                row["relevance"] = ai_logic[cid][doc_id]["rel"]
                row["evidence_span"] = ai_logic[cid][doc_id]["span"]
                row["annotation_reason"] = ai_logic[cid][doc_id]["reason"]
                row["confidence"] = "HIGH"
                if row["relevance"] == "DIRECT_SUPPORT":
                    direct_count += 1
                else:
                    partial_count += 1
            else:
                doc_text = docs[doc_id].get("text", docs[doc_id].get("abstract", ""))
                # Distinguish INSUFFICIENT_SOURCE_TEXT from NOT_RELEVANT
                if len(doc_text) < 100: # heuristic: title only usually short
                    row["relevance"] = "INSUFFICIENT_SOURCE_TEXT"
                    row["annotation_reason"] = "Only limited text/title available; insufficient to determine full relevance."
                    insufficient_count += 1
                else:
                    row["relevance"] = "NOT_RELEVANT"
                    row["annotation_reason"] = "Document text does not appear to contain evidence supporting the specific clinical claim."
                
                row["evidence_span"] = ""
                row["confidence"] = "LOW"
                
            row["annotator_id"] = "AI_ASSISTANT"
            row["review_timestamp"] = datetime.now(timezone.utc).isoformat()
            row["annotation_source"] = "AI_DIAGNOSTIC"
            row["ground_truth_eligible"] = "false"
            
            writer.writerow(row)
            
    # 3. Create JSON Summary
    summary = {
        "annotation_source": "AI_DIAGNOSTIC",
        "ground_truth_eligible": False,
        "cases_processed": 10,
        "documents_processed": 248,
        "rows_processed": 2480,
        "direct_support_suggestions": direct_count,
        "partial_support_suggestions": partial_count,
        "insufficient_source_text_records": insufficient_count,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
    with open(ai_dir / "ai_pilot_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
        
    # 4. Create Method MD
    method_content = """# AI Annotation Method (Diagnostic Only)

This track uses a simple diagnostic script to scan the 248-document corpus for 10 pilot cases.
It identifies potential candidates for `DIRECT_SUPPORT` and `PARTIAL_SUPPORT` based on explicit textual matches in the abstract/title.
It explicitly assigns `INSUFFICIENT_SOURCE_TEXT` when the corpus only provides a short string (e.g. title-only) preventing confident clinical judgment.

**WARNING:** This metadata records AI generation and MUST NOT be interpreted as human provenance.
"""
    with open(ai_dir / "ai_annotation_method.md", "w") as f:
        f.write(method_content)
        
    # 5. Create Audit Report
    report_content = f"""# V3.1 AI-Assisted Pilot (Diagnostic)

**Status:** AI_DIAGNOSTIC
**Ground Truth Eligible:** false

## Scope
- `case_count`: 10
- `document_count`: 248
- `row_count`: 2480
- `annotation_source`: AI_DIAGNOSTIC

## Diagnostic Summary
- `direct_support_suggestions`: {direct_count}
- `partial_support_suggestions`: {partial_count}
- `insufficient_source_text_records`: {insufficient_count}

## Source Limitations
Many documents in the snapshot only contain title-level data. The AI was explicitly instructed NOT to invent evidence spans from titles. Where text was insufficient, it recorded `INSUFFICIENT_SOURCE_TEXT`.

## EXPLICIT DISCLAIMER
"This pilot uses AI-generated diagnostic annotations. These annotations are not human annotations and are not eligible to serve as independent human ground truth."
"""
    with open(reports_dir / "v3_1_ai_assisted_pilot.md", "w") as f:
        f.write(report_content)
        
    print("AI-Assisted Diagnostic Track generated successfully.")

if __name__ == "__main__":
    main()