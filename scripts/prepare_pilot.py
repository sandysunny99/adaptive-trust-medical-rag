import os
import shutil
import csv
import json
from pathlib import Path

def main():
    print("Preparing True Human Pilot...")
    
    # 1. Archive the invalid pilot separately
    archive_dir = Path("experiments/annotations/v3_1_human/archive/invalid_pilot")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    comp_dir = Path("experiments/annotations/v3_1_human/completed")
    man_dir = Path("experiments/manifests")
    script_dir = Path("scripts")
    
    # Move invalid files if they still exist in original locations
    f1 = comp_dir / "reviewer_A_INVALID_AS_HUMAN_ANNOTATION.csv"
    if f1.exists():
        shutil.move(str(f1), str(archive_dir / "reviewer_A_INVALID_AS_HUMAN_ANNOTATION.csv"))
        
    f2 = man_dir / "retrieval_ground_truth_v3_1_human_INVALID_AS_HUMAN_ANNOTATION.json"
    if f2.exists():
        shutil.move(str(f2), str(archive_dir / "retrieval_ground_truth_v3_1_human_INVALID_AS_HUMAN_ANNOTATION.json"))
        
    f3 = script_dir / "do_pilot_annotation_INVALID.py"
    if f3.exists():
        shutil.move(str(f3), str(archive_dir / "do_pilot_annotation_INVALID.py"))
        
    # Archive metadata
    with open(archive_dir / "README.md", "w") as f:
        f.write("# Invalid Pilot Archive\n\nThese artifacts were invalidated on 2026-09-03 because the relevance decisions were programmatically hard-coded in a python dictionary rather than entered by an independent human reviewer, violating the rule against automated label generation.\n")
        
    # 2. Create the 10-case blank pilot package
    pilot_dir = Path("experiments/annotations/v3_1_human/pilot")
    pilot_dir.mkdir(parents=True, exist_ok=True)
    (pilot_dir / "completed").mkdir(parents=True, exist_ok=True)
    
    pilot_cases = ["v3.1h-001", "v3.1h-002", "v3.1h-021", "v3.1h-022", "v3.1h-023", 
                   "v3.1h-046", "v3.1h-047", "v3.1h-066", "v3.1h-067", "v3.1h-069"]
                   
    review_csv = Path("experiments/annotations/v3_1_human/review.csv")
    pilot_csv = pilot_dir / "pilot_review.csv"
    
    written_rows = 0
    with open(review_csv, newline='', encoding='utf-8') as fin, \
         open(pilot_csv, "w", newline='', encoding='utf-8') as fout:
        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        for row in reader:
            if row["case_id"] in pilot_cases:
                # Ensure every annotation field is PENDING/empty
                assert row["relevance"] == "PENDING"
                assert row["evidence_span"] == ""
                assert row["annotation_reason"] == ""
                assert row["confidence"] == ""
                assert row["annotator_id"] == ""
                assert row["review_timestamp"] == ""
                
                # Verify no model rankings/scores are exposed in headers
                for h in reader.fieldnames:
                    assert "score" not in h.lower()
                    assert "rank" not in h.lower()
                    assert "bm25" not in h.lower()
                    assert "rrf" not in h.lower()
                    assert "medcpt" not in h.lower()
                    
                writer.writerow(row)
                written_rows += 1
                
    assert written_rows == len(pilot_cases) * 248
    print(f"Created pilot_review.csv with {written_rows} rows (10 cases * 248 documents).")
    
    # 3. Add pilot manifest
    manifest = {
        "pilot_version": "V3.1-HUMAN-PILOT-1",
        "case_count": 10,
        "annotation_mode": "SINGLE_REVIEWER",
        "status": "PENDING_HUMAN_REVIEW",
        "corpus": "retrieval-v3-real",
        "retrieval_evaluation_locked": True
    }
    with open(pilot_dir / "pilot_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        
    # 4. Add reviewer instructions
    instructions = """# V3.1-HUMAN Pilot Annotation Instructions

## Purpose
The purpose of this pilot is to validate the annotation process, workflow, and instructions before annotating the full 80-case dataset.

## Workspace
- The 248-document frozen corpus is located at: `experiments/evidence_snapshots/retrieval-v3-real/documents.json`
- The review template is: `pilot_review.csv`

## Workflow
1. Open `pilot_review.csv`. You have 10 cases (2,480 rows total).
2. For each case, search the frozen corpus or the document_text column for evidence.
3. If evidence is found, mark the row as `DIRECT_SUPPORT` or `PARTIAL_SUPPORT`.
   - You MUST copy the exact contiguous `evidence_span` from the source text.
   - You MUST provide an `annotation_reason`.
   - Provide `confidence` (HIGH, MEDIUM, LOW), `annotator_id`, and `review_timestamp` (UTC ISO-8601).
4. For all other reviewed candidate documents that do not provide evidence, mark `NOT_RELEVANT`.
5. Only if you have searched the corpus and conclude there is no evidence available for the query, mark exactly one row for that case as `NO_EVIDENCE`.
6. Save your completed file in `completed/reviewer_A.csv`. Do NOT overwrite the blank `pilot_review.csv`.

## Rules
- DDI: Require actual interaction evidence (A affects B), not just co-occurrence.
- ADE: Require evidence connecting drug to adverse event. Respect negation (e.g., 'no association').
- Pharmacology: Match the exact requested concept (mechanism, clearance, etc.).
- Medication Safety: Match the exact safety question (renal dosing, etc.).
"""
    with open(pilot_dir / "pilot_instructions.md", "w") as f:
        f.write(instructions)
        
    print("Pilot workspace prepared. Waiting for human.")

if __name__ == "__main__":
    main()