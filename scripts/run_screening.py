import csv
import json
import random
import hashlib
import os
from pathlib import Path

def update_docs():
    amend_path = Path("reports/audit/v3_1_annotation_protocol_amendment.md")
    if amend_path.exists():
        content = amend_path.read_text(encoding="utf-8")
        
        # Replace Rule 3
        old_rule_3 = "### 3. False Negative Checking\nA random sampling of 5% of the \"unsurfaced\" corpus for each case must be subjected to an automated secondary LLM review. If this secondary review flags any document as potentially relevant, it must be escalated to a human. If no relevant documents are found in the sample, the unsurfaced corpus is presumed negative."
        new_rule_3 = """### 3. False Negative Checking
A random sampling of exactly 5% of the "unsurfaced" corpus for each case must be subjected to an automated secondary screening using a reproducible random seed. 
The 5% sample is a **screening/assurance mechanism**, not independent proof of negative ground truth.
Allowed outputs from the screening are `POTENTIALLY_RELEVANT`, `UNCERTAIN`, and `PROBABLY_IRRELEVANT`.
Every `POTENTIALLY_RELEVANT` or `UNCERTAIN` result MUST be escalated to the human reviewer for independent adjudication.

### 3b. Critical Interpretation Rule
Never state that the 5% sample proved the remaining 95% is irrelevant, nor that no relevant documents exist in the unsurfaced corpus, unless the entire corpus was actually reviewed.
Instead, state: "No potentially relevant documents were identified in the sampled unsurfaced corpus under the specified secondary screening procedure, and all flagged/uncertain records were escalated to human review."
"""
        content = content.replace(old_rule_3, new_rule_3)
        amend_path.write_text(content, encoding="utf-8")

    spec_content = """# Phase 2F.3 Candidate-Based Validation Specification

## 1. Candidate Generation
Candidates are surfaced using high-recall, multi-strategy methods (e.g., BM25, dense vector, entity graphs).

## 2. False-Negative Screening Procedure
For each case:
1. Define `unsurfaced_documents = frozen_corpus - surfaced_candidates`.
2. Select exactly 5% of the unsurfaced documents using a reproducible random seed (seed=42).
3. Record `case_id`, `population_size`, `sample_size`, `sampling_seed`, `sampled_document_ids`.
4. Run automated secondary screening to yield `POTENTIALLY_RELEVANT`, `UNCERTAIN`, or `PROBABLY_IRRELEVANT`. (No final human labels).
5. Escalate every `POTENTIALLY_RELEVANT` or `UNCERTAIN` result to the human reviewer.
6. The human reviewer independently adjudicates every escalated document (`DIRECT_SUPPORT`, `PARTIAL_SUPPORT`, `NOT_RELEVANT`, `NO_EVIDENCE`).

## 3. Case Closure
A case is formally `CASE_PROTOCOL_COMPLETE` only when:
A. All surfaced candidates have human decisions.
B. The 5% secondary screening has been executed with reproducible sampling metadata.
C. Every `POTENTIALLY_RELEVANT` or `UNCERTAIN` result has been reviewed by the human.
D. The reviewer confirms `NEW_EVIDENCE = NONE IDENTIFIED`.

## 4. Ground Truth Limitations
The un-sampled 95% remainder remains explicitly `UNSURFACED_REMAINDER` / `NOT_INDIVIDUALLY_HUMAN_REVIEWED` and cannot be bulk-labeled as `NOT_RELEVANT`.
"""
    Path("reports/audit/v3_1_candidate_based_validation_spec.md").write_text(spec_content, encoding="utf-8")

def run_screening():
    with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json", "r", encoding="utf-8") as f:
        corpus = json.load(f)
    
    all_doc_ids = [str(d["document_id"]) for d in corpus]
    doc_lookup = {str(d["document_id"]): d for d in corpus}
    
    workspace = Path("experiments/annotations/v3_1_human/pilot/reviewer_workspace")
    in_csv = workspace / "decision_helper_review.csv"
    out_dir = Path("experiments/annotations/v3_1_human/pilot/false_negative_screen")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    cases = {}
    with open(in_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["case_id"]
            if cid not in cases:
                cases[cid] = {"query": row["query"], "surfaced": []}
            cases[cid]["surfaced"].append(str(row["document_id"]))
            
    # Simple stop words for rudimentary screening
    stop_words = set(["the", "a", "an", "and", "or", "but", "of", "in", "with", "between", "on", "to", "for", "is", "are", "was", "were", "induced", "use", "risk", "patients"])

    report_lines = [
        "# Phase 2F.3 False-Negative Screen Report\n",
        "| Case | Population | Sample | Flagged | Uncertain | Escalations | Status |",
        "|------|------------|--------|---------|-----------|-------------|--------|"
    ]
    
    escalations = []

    for cid, data in cases.items():
        surfaced = set(data["surfaced"])
        unsurfaced = [did for did in all_doc_ids if did not in surfaced]
        
        # 5% sample
        sample_size = round(len(unsurfaced) * 0.05)
        random.seed(42 + int(hashlib.md5(cid.encode()).hexdigest(), 16) % (10**8))
        sampled = random.sample(unsurfaced, sample_size)
        
        query_words = set([w.lower() for w in data["query"].split() if w.lower() not in stop_words])
        
        results = []
        flagged_count = 0
        uncertain_count = 0
        
        for did in sampled:
            doc = doc_lookup[did]
            text = (doc.get("title", "") + " " + doc.get("abstract", "")).lower()
            
            overlap = sum(1 for qw in query_words if qw in text)
            
            if overlap >= 2:
                status = "POTENTIALLY_RELEVANT"
                flagged_count += 1
            elif overlap == 1:
                status = "UNCERTAIN"
                uncertain_count += 1
            else:
                status = "PROBABLY_IRRELEVANT"
                
            results.append({
                "document_id": did,
                "title": doc.get("title", ""),
                "status": status,
                "overlap": overlap
            })
            
            if status in ["POTENTIALLY_RELEVANT", "UNCERTAIN"]:
                escalations.append({
                    "case_id": cid,
                    "document_id": did,
                    "title": doc.get("title", ""),
                    "status": status,
                    "query": data["query"]
                })
                
        # Write JSON
        out_json = out_dir / f"{cid}_screen.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump({
                "case_id": cid,
                "population_size": len(unsurfaced),
                "sample_size": sample_size,
                "sampling_seed": 42 + int(hashlib.md5(cid.encode()).hexdigest(), 16) % (10**8),
                "sampled_document_ids": sampled,
                "screening_results": results,
                "human_escalations": [r["document_id"] for r in results if r["status"] in ["POTENTIALLY_RELEVANT", "UNCERTAIN"]],
                "human_final_decisions": {}
            }, f, indent=2)
            
        report_lines.append(f"| {cid} | {len(unsurfaced)} | {sample_size} | {flagged_count} | {uncertain_count} | {flagged_count + uncertain_count} | PENDING_ESCALATION_REVIEW |")
        
    report_lines.append("\n## Escalated Documents Pending Human Review\n")
    if not escalations:
        report_lines.append("No documents were flagged for human escalation across all sampled cases.")
    else:
        for esc in escalations:
            report_lines.append(f"### Case: {esc['case_id']} | Document: {esc['document_id']}")
            report_lines.append(f"**Query:** {esc['query']}")
            report_lines.append(f"**Title:** {esc['title']}")
            report_lines.append(f"**Screening Status:** {esc['status']}\n")
            
    Path("reports/audit/v3_1_false_negative_screen_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(f"Total escalations: {len(escalations)}")

if __name__ == "__main__":
    update_docs()
    run_screening()