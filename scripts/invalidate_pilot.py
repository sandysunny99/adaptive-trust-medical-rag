import os
import shutil
from pathlib import Path

def main():
    print("Invalidating programmatic pilot...")
    
    ann_dir = Path("experiments/annotations/v3_1_human/completed")
    pilot_csv = ann_dir / "reviewer_A.csv"
    if pilot_csv.exists():
        pilot_csv.rename(ann_dir / "reviewer_A_INVALID_AS_HUMAN_ANNOTATION.csv")
        
    man_dir = Path("experiments/manifests")
    gt_json = man_dir / "retrieval_ground_truth_v3_1_human.json"
    if gt_json.exists():
        gt_json.rename(man_dir / "retrieval_ground_truth_v3_1_human_INVALID_AS_HUMAN_ANNOTATION.json")
        
    scripts_dir = Path("scripts")
    pilot_script = scripts_dir / "do_pilot_annotation.py"
    if pilot_script.exists():
        pilot_script.rename(scripts_dir / "do_pilot_annotation_INVALID.py")
        
    # Create integrity failure report
    report = """# V3.1 Human Annotation Pilot Integrity Failure

**Status:**
INVALID HUMAN ANNOTATION EVIDENCE

**Reason:**
The submitted annotation decisions were generated programmatically from a hard-coded annotation dictionary in `scripts/do_pilot_annotation.py` rather than entered by an independent human reviewer.

**Impact:**
The resulting JSON cannot be used as independently curated ground truth because it violates the core rule against programmatic relevance generation.

**Decision:**
V3.1 confirmation remains blocked. The generated files have been preserved but renamed with `INVALID_AS_HUMAN_ANNOTATION` to prevent accidental usage.
"""
    reports_dir = Path("reports/audit")
    reports_dir.mkdir(parents=True, exist_ok=True)
    with open(reports_dir / "v3_1_human_annotation_pilot_integrity_failure.md", "w") as f:
        f.write(report)
        
    # Create reviewer package
    pkg_dir = Path("experiments/annotations/v3_1_human/reviewer_package")
    pkg_dir.mkdir(parents=True, exist_ok=True)
    
    src_dir = Path("experiments/annotations/v3_1_human")
    if (src_dir / "review.csv").exists():
        shutil.copy(src_dir / "review.csv", pkg_dir / "review.csv")
    if (src_dir / "annotation_guide.md").exists():
        shutil.copy(src_dir / "annotation_guide.md", pkg_dir / "annotation_guide.md")
    if (src_dir / "README.md").exists():
        shutil.copy(src_dir / "README.md", pkg_dir / "README.md")
        
    print("Invalidation complete. Reviewer package staged.")

if __name__ == "__main__":
    main()