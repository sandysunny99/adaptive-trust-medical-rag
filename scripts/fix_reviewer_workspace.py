import csv
import json
from pathlib import Path

def main():
    print("Fixing Human Review Workspace...")
    
    workspace_dir = Path("experiments/annotations/v3_1_human/pilot/reviewer_workspace")
    workspace_dir.mkdir(parents=True, exist_ok=True)
    
    reports_dir = Path("reports/audit")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    in_csv = Path("experiments/annotations/v3_1_human/ai_diagnostic/ai_pilot_review.csv")
    out_csv = workspace_dir / "candidate_evidence.csv"
    
    # Load corpus to check text length
    with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json", encoding="utf-8") as f:
        docs = {d["document_id"]: d for d in json.load(f)}
        
    case_order = ["v3.1h-001", "v3.1h-002", "v3.1h-021", "v3.1h-022", "v3.1h-023", 
                  "v3.1h-046", "v3.1h-047", "v3.1h-066", "v3.1h-067", "v3.1h-069"]
    
    candidates_by_case = {c: [] for c in case_order}
    direct_counts = {c: 0 for c in case_order}
    partial_counts = {c: 0 for c in case_order}
    limited_text_count = 0
    full_text_count = 0
    
    fields = [
        "case_id", "query", "claim_type", "risk_tier", "difficulty",
        "document_id", "chunk_id", "document_title", "document_text",
        "ai_suggested_label", "ai_suggested_evidence", "ai_suggested_reason",
        "human_final_label", "human_evidence_span", "human_annotation_reason",
        "human_confidence", "human_agreement", "human_annotator_id", "human_review_timestamp"
    ]
    
    with open(in_csv, newline='', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        for row in reader:
            lbl = row.get("relevance", "")
            if lbl in ["DIRECT_SUPPORT", "PARTIAL_SUPPORT"]:
                cid = row["case_id"]
                if lbl == "DIRECT_SUPPORT":
                    direct_counts[cid] += 1
                else:
                    partial_counts[cid] += 1
                    
                doc_id = row["document_id"]
                doc_text = docs[doc_id].get("text", docs[doc_id].get("abstract", ""))
                
                # Check limited text
                if len(doc_text) < 100:
                    doc_text = "[SOURCE_TEXT_LIMITED] " + doc_text
                    limited_text_count += 1
                else:
                    full_text_count += 1
                
                new_row = {
                    "case_id": row["case_id"],
                    "query": row["query"],
                    "claim_type": row["claim_type"],
                    "risk_tier": row["risk_tier"],
                    "difficulty": row["difficulty"],
                    "document_id": doc_id,
                    "chunk_id": row["chunk_id"],
                    "document_title": row["document_title"],
                    "document_text": doc_text,
                    "ai_suggested_label": lbl,
                    "ai_suggested_evidence": row.get("evidence_span", ""),
                    "ai_suggested_reason": row.get("annotation_reason", ""),
                    "human_final_label": "",
                    "human_evidence_span": "",
                    "human_annotation_reason": "",
                    "human_confidence": "",
                    "human_agreement": "",
                    "human_annotator_id": "",
                    "human_review_timestamp": ""
                }
                candidates_by_case[cid].append(new_row)
                
    total_candidates = sum(direct_counts.values()) + sum(partial_counts.values())
    
    with open(out_csv, "w", newline='', encoding='utf-8') as fout:
        writer = csv.DictWriter(fout, fieldnames=fields)
        writer.writeheader()
        for cid in case_order:
            for r in candidates_by_case[cid]:
                writer.writerow(r)
                
    report_content = f"""# V3.1 Reviewer Workspace Status

## Overview
- **Total AI Candidates Surfaced**: {total_candidates}
- **Source Text Available (Full)**: {full_text_count}
- **Source Text Limited (Title/Short)**: {limited_text_count}

## Breakdown per Case
"""
    for cid in case_order:
        report_content += f"- **{cid}**: {direct_counts[cid] + partial_counts[cid]} (DIRECT: {direct_counts[cid]}, PARTIAL: {partial_counts[cid]})\n"

    with open(reports_dir / "v3_1_reviewer_workspace_status.md", "w") as f:
        f.write(report_content)
        
    print(f"Actual AI candidate count: {total_candidates}")
    for cid in case_order:
        print(f"{cid} = {direct_counts[cid] + partial_counts[cid]}")
    print(f"File created: {out_csv}")

if __name__ == "__main__":
    main()