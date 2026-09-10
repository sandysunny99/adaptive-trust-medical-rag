import csv
import json
from pathlib import Path

def main():
    print("Building Human Review Workflow...")
    
    workspace_dir = Path("experiments/annotations/v3_1_human/pilot/reviewer_workspace")
    workspace_dir.mkdir(parents=True, exist_ok=True)
    
    reports_dir = Path("reports/audit")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    in_csv = Path("experiments/annotations/v3_1_human/ai_diagnostic/ai_pilot_review.csv")
    out_csv = workspace_dir / "reviewer_A_case_review.csv"
    prog_csv = workspace_dir / "review_progress.csv"
    
    # 1. Proposal for scope reduction
    proposal_content = """# V3.1 Pilot Scope Proposal

## Current Requirement
The frozen validation specification currently requires a completed decision for every single case-document pair.
For the 10-case pilot, this equates to exactly **2,480 row-level judgments**.

## Operational Bottleneck
Forcing a human reviewer to manually mark `NOT_RELEVANT` across thousands of topically-unrelated background documents is extremely expensive and causes annotator fatigue, degrading the quality of the positive-evidence review.

## Proposed Reduction
If the research protocol allows, we propose modifying the validator (`scripts/validate_v3_1_human_submission.py`) to accept a **Candidate Verification Mode**:
1. The human reviewer explicitly annotates the identified candidate documents and any newly discovered evidence.
2. The human explicitly approves a case-level closure (e.g. marking the remaining unannotated candidates as assumed `NOT_RELEVANT` implicitly, or explicitly via a script AFTER human sign-off).
3. The human may assign `NO_EVIDENCE` at the case level if they conclude the candidates and manual searches yielded no support.

## Decision Required
Until this proposal is formally approved and the validator is updated, Anti-Gravity will enforce the strict 2,480-row requirement. We await your explicit approval to implement this reduction.
"""
    with open(reports_dir / "v3_1_pilot_scope_proposal.md", "w") as f:
        f.write(proposal_content)
        
    # 2. Build Case Review File & Progress
    case_order = ["v3.1h-001", "v3.1h-002", "v3.1h-021", "v3.1h-022", "v3.1h-023", 
                  "v3.1h-046", "v3.1h-047", "v3.1h-066", "v3.1h-067", "v3.1h-069"]
                  
    # Group by case, prioritize AI suggestions (DIRECT/PARTIAL)
    grouped_rows = {c: [] for c in case_order}
    
    fields = [
        "case_id", "query", "claim_type", "risk_tier", "difficulty",
        "document_id", "chunk_id", "document_title", "document_text",
        "---AI_SUGGESTION---",
        "ai_suggested_label", "ai_suggested_evidence", "ai_suggested_reason",
        "---HUMAN_DECISION---",
        "human_final_label", "human_evidence_span", "human_annotation_reason",
        "human_confidence", "human_agreement", "human_annotator_id", "human_review_timestamp"
    ]
    
    with open(in_csv, newline='', encoding='utf-8') as fin:
        reader = csv.DictReader(fin)
        for row in reader:
            if row["case_id"] in grouped_rows:
                new_row = {f: row.get(f, "") for f in fields if not f.startswith("---")}
                new_row["---AI_SUGGESTION---"] = ""
                new_row["---HUMAN_DECISION---"] = ""
                # Initialize human fields blank
                for h in ["human_final_label", "human_evidence_span", "human_annotation_reason", "human_confidence", "human_agreement", "human_annotator_id", "human_review_timestamp"]:
                    new_row[h] = ""
                    
                # Store it
                grouped_rows[row["case_id"]].append(new_row)
                
    # Sort each case: AI suggestions first
    candidates_surfaced = {}
    with open(out_csv, "w", newline='', encoding='utf-8') as fout:
        writer = csv.DictWriter(fout, fieldnames=fields)
        writer.writeheader()
        
        for cid in case_order:
            rows = grouped_rows[cid]
            # Prioritize DIRECT_SUPPORT or PARTIAL_SUPPORT
            candidates = [r for r in rows if r["ai_suggested_label"] in ["DIRECT_SUPPORT", "PARTIAL_SUPPORT"]]
            others = [r for r in rows if r["ai_suggested_label"] not in ["DIRECT_SUPPORT", "PARTIAL_SUPPORT"]]
            candidates_surfaced[cid] = len(candidates)
            
            # Write candidates, then a few examples, or just all
            for r in candidates + others:
                writer.writerow(r)
                
    # 3. Create Progress Tracker
    prog_fields = ["case_id", "documents_reviewed", "human_decisions_completed", "positive_decisions", "partial_decisions", "not_relevant_decisions", "no_evidence_decisions", "remaining", "status"]
    with open(prog_csv, "w", newline='', encoding='utf-8') as fout:
        writer = csv.DictWriter(fout, fieldnames=prog_fields)
        writer.writeheader()
        for cid in case_order:
            writer.writerow({
                "case_id": cid,
                "documents_reviewed": 0,
                "human_decisions_completed": 0,
                "positive_decisions": 0,
                "partial_decisions": 0,
                "not_relevant_decisions": 0,
                "no_evidence_decisions": 0,
                "remaining": 248,
                "status": "PENDING"
            })
            
    # 4. Reviewer Instructions
    instructions = """# Human Review Workflow & Instructions

## Workflow
1. Open `reviewer_A_case_review.csv`. It is grouped by `case_id`.
2. For each case, the strongest AI-surfaced candidates appear at the top.
3. Read the query and the actual frozen source text (`document_text` or via `documents.json`).
4. **MAKE YOUR INDEPENDENT DECISION.** Do not blindly trust the AI suggestion.
5. Fill out the `human_` fields (label, evidence span, rationale, confidence, agreement, reviewer ID, timestamp).
6. Update `review_progress.csv` manually as a tracker if desired.

## AI Suggestions vs Human Fields
Visually, the file separates `---AI_SUGGESTION---` and `---HUMAN_DECISION---`. The human decision fields MUST be filled.

## Adding Missing Evidence
If the AI missed a document and you found it manually in the corpus: simply find its row in the file or append a new row, and mark `human_agreement = NEW_EVIDENCE`.

## Note on Current Requirements
Currently, the frozen protocol demands all 2,480 rows be explicitly labeled. See `reports/audit/v3_1_pilot_scope_proposal.md` for a pending proposal to reduce this burden.
"""
    with open(workspace_dir / "review_instructions.md", "w") as f:
        f.write(instructions)
        
    print(f"Workspace path: {workspace_dir}")
    print("Candidates surfaced per case:")
    for c, count in candidates_surfaced.items():
        print(f"  {c}: {count} candidate(s)")
    print("Remaining human workload: 10 cases (2,480 total row-level judgments, pending scope reduction approval)")

if __name__ == "__main__":
    main()