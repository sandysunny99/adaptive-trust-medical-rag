import csv
import json
import random
import os
import hashlib
from pathlib import Path
import shutil

def get_corpus_hash(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha256.update(chunk)
    return sha256.hexdigest()

def main():
    base_dir = Path("experiments/annotations/v3_1_human/pilot")
    v1_dir = base_dir / "false_negative_screen"
    v1_archive = base_dir / "false_negative_screen_v1"
    v2_dir = base_dir / "false_negative_screen_v2"
    
    audit_dir = Path("reports/audit")
    v1_report = audit_dir / "v3_1_false_negative_screen_report.md"
    v1_report_archive = audit_dir / "v3_1_false_negative_screen_report_v1.md"
    v2_report = audit_dir / "v3_1_false_negative_screen_report_v2.md"
    compare_report = audit_dir / "v3_1_false_negative_screen_v1_v2_comparison.md"
    
    # 1 & 2. Archive V1
    if v1_dir.exists() and not v1_archive.exists():
        shutil.move(str(v1_dir), str(v1_archive))
    if v1_report.exists() and not v1_report_archive.exists():
        shutil.copy(str(v1_report), str(v1_report_archive))
        
    v2_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. Compute corpus hash
    corpus_path = "experiments/evidence_snapshots/retrieval-v3-real/documents.json"
    corpus_hash = get_corpus_hash(corpus_path)
    
    # 4. Generate manifest
    manifest = {
        "protocol_version": "V3.1-FN-SCREEN-V2",
        "sampling_rate": 0.05,
        "base_seed": 42,
        "seed_method": "SHA256(case_id)",
        "corpus_hash": corpus_hash,
        "candidate_source": "experiments/annotations/v3_1_human/pilot/reviewer_workspace/decision_helper_review.csv",
        "screening_method": "AUTOMATED_TRIAGE",
        "final_human_label_generation": False
    }
    with open(v2_dir / "screen_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        
    # 5-9. Run V2 Screening
    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)
        
    all_doc_ids = [str(d["document_id"]) for d in corpus]
    doc_lookup = {str(d["document_id"]): d for d in corpus}
    
    in_csv = base_dir / "reviewer_workspace/decision_helper_review.csv"
    cases = {}
    with open(in_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["case_id"]
            if cid not in cases:
                cases[cid] = {"query": row["query"], "surfaced": []}
            cases[cid]["surfaced"].append(str(row["document_id"]))
            
    stop_words = set(["the", "a", "an", "and", "or", "but", "of", "in", "with", "between", "on", "to", "for", "is", "are", "was", "were", "induced", "use", "risk", "patients"])

    v2_report_lines = [
        "# Phase 2F.3 False-Negative Screen Report (V2)\n",
        "| Case | Population | Sample | Probably Irrelevant | Uncertain | Potentially Relevant | Escalations |",
        "|------|------------|--------|---------------------|-----------|----------------------|-------------|"
    ]
    
    human_queue = []
    v2_data = {}
    
    for cid, data in cases.items():
        surfaced = set(data["surfaced"])
        # Ensure deterministic ordering
        unsurfaced = sorted([did for did in all_doc_ids if did not in surfaced])
        
        sample_size = round(len(unsurfaced) * 0.05)
        
        # Deterministic seed
        seed_material = f"v3.1-fn-screen-v2:{cid}".encode("utf-8")
        seed = 42 + int.from_bytes(hashlib.sha256(seed_material).digest()[:8], "big") % (10**8)
        
        random.seed(seed)
        sampled = random.sample(unsurfaced, sample_size)
        
        query_words = set([w.lower() for w in data["query"].split() if w.lower() not in stop_words])
        
        results = []
        c_prob_irr = 0
        c_unc = 0
        c_pot_rel = 0
        
        for did in sampled:
            doc = doc_lookup[did]
            text = (doc.get("title", "") + " " + doc.get("abstract", "")).lower()
            overlap = sum(1 for qw in query_words if qw in text)
            
            if overlap >= 2:
                status = "POTENTIALLY_RELEVANT"
                c_pot_rel += 1
            elif overlap == 1:
                status = "UNCERTAIN"
                c_unc += 1
            else:
                status = "PROBABLY_IRRELEVANT"
                c_prob_irr += 1
                
            results.append({
                "document_id": did,
                "title": doc.get("title", ""),
                "status": status,
                "overlap": overlap
            })
            
            if status in ["POTENTIALLY_RELEVANT", "UNCERTAIN"]:
                human_queue.append({
                    "case_id": cid,
                    "document_id": did,
                    "title": doc.get("title", ""),
                    "query": data["query"],
                    "screening_status": status,
                    "human_final_label": "",
                    "human_evidence_span": "",
                    "human_annotation_reason": "",
                    "human_confidence": "",
                    "human_annotator_id": "",
                    "human_review_timestamp": ""
                })
                
        out_json = v2_dir / f"{cid}_screen.json"
        case_out = {
            "case_id": cid,
            "population_size": len(unsurfaced),
            "sample_size": sample_size,
            "sampling_seed": seed,
            "sampled_document_ids": sampled,
            "screening_results": results,
            "human_escalations": [r["document_id"] for r in results if r["status"] in ["POTENTIALLY_RELEVANT", "UNCERTAIN"]],
            "human_final_decisions": {}
        }
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(case_out, f, indent=2)
            
        v2_data[cid] = case_out
        escalations_count = c_unc + c_pot_rel
        v2_report_lines.append(f"| {cid} | {len(unsurfaced)} | {sample_size} | {seed} | {c_prob_irr} | {c_unc} | {c_pot_rel} | {escalations_count} |")
        
    v2_report.write_text("\n".join(v2_report_lines), encoding="utf-8")
    
    # 8. Human Review Queue CSV
    queue_fields = ["case_id", "document_id", "title", "query", "screening_status", "human_final_label", "human_evidence_span", "human_annotation_reason", "human_confidence", "human_annotator_id", "human_review_timestamp"]
    with open(v2_dir / "human_review_queue.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=queue_fields)
        writer.writeheader()
        for row in human_queue:
            writer.writerow(row)
            
    # 11. Compare V1 and V2
    comp_lines = [
        "# V1 vs V2 False-Negative Screen Comparison",
        "Note: V1 and V2 are different sampling runs due to seed corrections. V2 is the authoritative reproducible screening run. V1 remains historical audit evidence only.",
        ""
    ]
    
    for cid in cases.keys():
        v1_path = v1_archive / f"{cid}_screen.json"
        v2_path = v2_dir / f"{cid}_screen.json"
        
        v1_data = json.loads(v1_path.read_text(encoding="utf-8")) if v1_path.exists() else None
        v2_case = v2_data[cid]
        
        comp_lines.append(f"## Case {cid}")
        if v1_data:
            comp_lines.append(f"- **V1 Seed:** {v1_data.get('sampling_seed')} | **V2 Seed:** {v2_case['sampling_seed']}")
            comp_lines.append(f"- **V1 Sample Size:** {v1_data.get('sample_size')} | **V2 Sample Size:** {v2_case['sample_size']}")
            comp_lines.append(f"- **V1 Escalations:** {v1_data.get('human_escalations', [])}")
            comp_lines.append(f"- **V2 Escalations:** {v2_case['human_escalations']}")
            comp_lines.append(f"- **Samples Match?:** {set(v1_data.get('sampled_document_ids', [])) == set(v2_case['sampled_document_ids'])}")
        else:
            comp_lines.append("V1 data not found.")
        comp_lines.append("")
        
    compare_report.write_text("\n".join(comp_lines), encoding="utf-8")

if __name__ == "__main__":
    main()