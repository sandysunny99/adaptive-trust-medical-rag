from pathlib import Path

def main():
    print("Generating Human Review Completion Matrix...")
    
    reports_dir = Path("reports/audit")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report = """# V3.1 Human Pilot Review Summary & Workload Matrix

**Status:** IN_PROGRESS
**Ground Truth Independence:** NOT_YET_ESTABLISHED

## 1. Human Review Status
The human analyst has reviewed the external AI diagnostic report and established authoritative guidance for the 10 pilot cases, specifically identifying the primary strong candidate documents that require `DIRECT_SUPPORT` upon verification.

However, the official validation specification requires a complete matrix:
* **Total required decisions**: 2,480 (10 cases × 248 documents)
* **Candidate documents verified**: ~10-20 (the high-signal PMIDs explicitly reviewed by the human)
* **Unreviewed documents**: ~2,460

## 2. Human Review Workload Matrix

| Case ID | Query | Total Rows | Human Reviewed (Candidates) | Remaining PENDING |
|---------|-------|------------|-----------------------------|-------------------|
| v3.1h-001 | Metformin hepatic gluconeogenesis | 248 | ~1-3 | ~245 |
| v3.1h-002 | Lisinopril clearance | 248 | ~1-3 | ~245 |
| v3.1h-021 | Warfarin + aspirin bleeding | 248 | ~1-3 | ~245 |
| v3.1h-022 | CYP2C9 fluconazole + warfarin | 248 | ~1-3 | ~245 |
| v3.1h-023 | Spironolactone + lisinopril | 248 | ~1-3 | ~245 |
| v3.1h-046 | Idiosyncratic DILI mechanisms | 248 | ~1-3 | ~245 |
| v3.1h-047 | Spironolactone hyperkalemia | 248 | ~1-3 | ~245 |
| v3.1h-066 | Metformin renal contraindication | 248 | ~1-3 | ~245 |
| v3.1h-067 | Warfarin INR monitoring | 248 | ~1-3 | ~245 |
| v3.1h-069 | DILI diagnosis | 248 | ~1-3 | ~245 |
| **TOTAL** | | **2,480** | **~10-30** | **~2,450** |

## 3. Critical Integrity Principle Applied
Anti-Gravity has strictly enforced the rule: **Do NOT fabricate decisions for unreviewed rows.** 
Because the human review covered the candidate documents but did not assign explicit `NOT_RELEVANT` or `NO_EVIDENCE` labels to the remaining 2,450 rows in a submitted file, the pilot remains **INCOMPLETE**. The AI diagnostic suggestions have NOT been automatically copied into the human submission.

## 4. Next Steps
To pass the Anti-Gravity validation gate (`scripts/validate_v3_1_human_submission.py`), an actual `reviewer_A.csv` must be supplied where all 2,480 rows contain valid human labels (with NO `PENDING` states). 

Until this file is completed and passes validation:
* `PHASE_2F.2` = IN_PROGRESS
* `PHASE_2F.3` = BLOCKED
* `F0 / F3` = LOCKED
"""
    with open(reports_dir / "v3_1_human_pilot_review_summary.md", "w") as f:
        f.write(report)
        
    print("Matrix generated successfully.")

if __name__ == "__main__":
    main()