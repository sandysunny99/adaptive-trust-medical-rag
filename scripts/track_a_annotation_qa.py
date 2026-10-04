import json
import os
import sys

def run_qa(workspace_file):
    if not os.path.exists(workspace_file):
        print(f"Workspace not found: {workspace_file}")
        return
        
    records = []
    with open(workspace_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            records.append(json.loads(line))
            
    errors = []
    warnings = []
    
    pos_ids = set()
    query_pos_pairs = set()
    
    valid_states = ["UNANNOTATED", "IN_PROGRESS", "ANNOTATED", "QA_FLAGGED", "QA_RESOLVED", "FROZEN"]
    valid_grades = [0, 1, 2, None]
    valid_labels = ["RELEVANT", "PARTIALLY_RELEVANT", "IRRELEVANT", "INSUFFICIENT_INFORMATION", "AMBIGUOUS", None]
    
    for idx, r in enumerate(records):
        pid = r.get("position_id")
        qid = r.get("query_id")
        
        if not pid: errors.append(f"Row {idx}: Missing position_id")
        if not qid: errors.append(f"Row {idx}: Missing query_id")
        
        if pid in pos_ids:
            errors.append(f"Row {idx}: Duplicate position_id {pid}")
        pos_ids.add(pid)
        
        pair = f"{qid}::{pid}"
        if pair in query_pos_pairs:
            errors.append(f"Row {idx}: Duplicate query_id/position_id pair {pair}")
        query_pos_pairs.add(pair)
        
        if r.get("schema_version") != "2.0.0":
            errors.append(f"Row {idx}: Invalid schema version {r.get('schema_version')}")
            
        status = r.get("annotation_status")
        if status not in valid_states:
            errors.append(f"Row {idx}: Invalid annotation_status {status}")
            
        if "rank" in r:
            errors.append(f"Row {idx}: Rank field should not be present.")
            
        if not r.get("retrieved_evidence") and r.get("original_evidence_available"):
            errors.append(f"Row {idx}: Evidence lost.")
            
        if status in ["ANNOTATED", "FROZEN", "QA_RESOLVED"]:
            if r.get("annotator_id") is None:
                errors.append(f"Row {idx}: Missing annotator_id for completed annotation")
            if r.get("timestamp") is None:
                errors.append(f"Row {idx}: Missing timestamp for completed annotation")
            if r.get("label") not in valid_labels:
                errors.append(f"Row {idx}: Invalid label {r.get('label')}")
            if r.get("relevance_grade") not in valid_grades:
                errors.append(f"Row {idx}: Invalid grade {r.get('relevance_grade')}")
                
        if r.get("abstract_available") is False and r.get("label") and r.get("label") != "INSUFFICIENT_INFORMATION":
            warnings.append(f"Row {idx}: Abstract missing but label is {r.get('label')}")
            
    out = {
        "total_records": len(records),
        "errors_count": len(errors),
        "warnings_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
        "status": "PASS" if not errors else "FAIL"
    }
    
    qa_json_path = "track_a_annotation/qa/TRACK_A_ANNOTATION_QA_V1.json"
    qa_md_path = "track_a_annotation/qa/TRACK_A_ANNOTATION_QA_V1.md"
    
    with open(qa_json_path, "w") as f:
        json.dump(out, f, indent=2)
        
    md = f"# TRACK_A_ANNOTATION_QA_V1\n\n"
    md += f"**Status**: {out['status']}\n"
    md += f"**Total Records Checked**: {out['total_records']}\n"
    md += f"**Errors**: {out['errors_count']}\n"
    md += f"**Warnings**: {out['warnings_count']}\n\n"
    md += "## QA Output\nNo errors found." if not errors else "## Errors\n" + "\n".join(f"- {e}" for e in errors)
    md += "\n\n## Warnings\nNo warnings found." if not warnings else "\n\n## Warnings\n" + "\n".join(f"- {w}" for w in warnings)
    
    with open(qa_md_path, "w") as f:
        f.write(md)
        
    print(f"QA complete. Errors: {out['errors_count']}, Warnings: {out['warnings_count']}")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else "track_a_annotation/annotator_a/TRACK_A_ANNOTATOR_A.jsonl"
    run_qa(target)
