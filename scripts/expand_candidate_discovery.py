import json
import csv
from pathlib import Path

def main():
    print("Expanding Candidate Discovery...")
    
    workspace_dir = Path("experiments/annotations/v3_1_human/pilot/reviewer_workspace")
    reports_dir = Path("reports/audit")
    
    with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json", encoding="utf-8") as f:
        docs = json.load(f)
        
    case_concepts = {
        "v3.1h-001": ["metformin", "hepatic glucose production", "hepatic gluconeogenesis", "ampk", "liver"],
        "v3.1h-002": ["lisinopril", "renal clearance", "renal elimination", "pharmacokinetics", "unchanged in urine"],
        "v3.1h-021": ["warfarin", "aspirin", "bleeding", "hemorrhage", "anticoagulation"],
        "v3.1h-022": ["fluconazole", "warfarin", "cyp2c9", "s-warfarin", "metabolism", "anticoagulant effect"],
        "v3.1h-023": ["spironolactone", "lisinopril", "ace inhibitor", "hyperkalemia", "potassium", "combination therapy"],
        "v3.1h-046": ["idiosyncratic", "drug-induced liver injury", "dili", "mechanism", "immune", "mitochondrial", "oxidative stress"],
        "v3.1h-047": ["spironolactone", "hyperkalemia", "potassium", "heart failure", "renal function"],
        "v3.1h-066": ["metformin", "renal impairment", "kidney function", "egfr", "contraindication", "lactic acidosis", "dose"],
        "v3.1h-067": ["warfarin", "inr", "international normalized ratio", "therapeutic range", "monitoring", "2.0", "3.0"],
        "v3.1h-069": ["drug-induced liver injury", "hepatotoxicity", "diagnosis", "dili", "rucam", "causality", "alternative causes"]
    }
    
    case_info = {
        "v3.1h-001": {"query": "How does metformin inhibit hepatic gluconeogenesis?", "claim": "Pharmacology", "risk": "R1", "diff": "MECHANISM"},
        "v3.1h-002": {"query": "Clearance pathway for lisinopril", "claim": "Pharmacology", "risk": "R1", "diff": "MECHANISM"},
        "v3.1h-021": {"query": "Concomitant use of warfarin and aspirin bleeding risk", "claim": "DDI", "risk": "R3", "diff": "MULTI_ENTITY"},
        "v3.1h-022": {"query": "CYP2C9 interaction between fluconazole and warfarin", "claim": "DDI", "risk": "R3", "diff": "CYP_DDI"},
        "v3.1h-023": {"query": "Spironolactone and lisinopril combination risks", "claim": "DDI", "risk": "R3", "diff": "MULTI_ENTITY"},
        "v3.1h-046": {"query": "Idiosyncratic drug induced liver injury mechanisms", "claim": "ADE", "risk": "R3", "diff": "MECHANISM"},
        "v3.1h-047": {"query": "Spironolactone induced hyperkalemia", "claim": "ADE", "risk": "R3", "diff": "SYNONYM"},
        "v3.1h-066": {"query": "Metformin contraindication in severe renal disease", "claim": "Medication_Safety", "risk": "R3", "diff": "PARAPHRASE"},
        "v3.1h-067": {"query": "Warfarin target INR monitoring", "claim": "Medication_Safety", "risk": "R3", "diff": "PARAPHRASE"},
        "v3.1h-069": {"query": "Diagnosis of drug induced hepatotoxicity", "claim": "Medication_Safety", "risk": "R3", "diff": "PARAPHRASE"}
    }
    
    candidates = []
    discovery_counts = {c: 0 for c in case_concepts}
    limited_counts = {c: 0 for c in case_concepts}
    
    for cid, terms in case_concepts.items():
        case_candidates = []
        for d in docs:
            text = d.get("text", d.get("abstract", "")).lower()
            title = d.get("title", "").lower()
            combined = title + " " + text
            
            # Simple scoring based on term presence
            score = sum(1 for t in terms if t in combined)
            if score > 0:
                doc_text = d.get("text", d.get("abstract", ""))
                availability = "TITLE_ONLY" if len(doc_text) < 100 else "FULL_TEXT"
                
                matched_terms = [t for t in terms if t in combined]
                reason = f"Candidate surfaced due to matching concepts: {', '.join(matched_terms)}."
                
                case_candidates.append({
                    "score": score,
                    "doc": d,
                    "reason": reason,
                    "availability": availability
                })
                
        # Sort by score desc, take top 15
        case_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = case_candidates[:15]
        
        for c in top_candidates:
            doc = c["doc"]
            candidates.append({
                "case_id": cid,
                "query": case_info[cid]["query"],
                "claim_type": case_info[cid]["claim"],
                "risk_tier": case_info[cid]["risk"],
                "difficulty": case_info[cid]["diff"],
                "document_id": doc["document_id"],
                "chunk_id": doc.get("chunk_id", f"{doc['document_id']}_c0"),
                "document_title": doc.get("title", ""),
                "document_text": doc.get("text", doc.get("abstract", "")),
                "candidate_reason": c["reason"],
                "source_text_availability": c["availability"]
            })
            discovery_counts[cid] += 1
            if c["availability"] == "TITLE_ONLY":
                limited_counts[cid] += 1
                
    out_csv = workspace_dir / "candidate_discovery.csv"
    fields = [
        "case_id", "query", "claim_type", "risk_tier", "difficulty",
        "document_id", "chunk_id", "document_title", "document_text",
        "candidate_reason", "source_text_availability"
    ]
    
    with open(out_csv, "w", newline='', encoding='utf-8') as fout:
        writer = csv.DictWriter(fout, fieldnames=fields)
        writer.writeheader()
        for c in candidates:
            writer.writerow(c)
            
    # Generate Report
    report = """# V3.1 Candidate Discovery Report

## Overview
This diagnostic pass surfaces evidence candidates based strictly on keyword, synonym, and biomedical concept matching within the frozen corpus. It does NOT generate final human relevance labels and does NOT use retrieval ranking models (F0/F3/MedCPT are locked).

## Discovery Counts per Case
| Case | Candidate Count | Title-Only Limited |
|------|-----------------|--------------------|
"""
    for cid in case_concepts:
        report += f"| {cid} | {discovery_counts[cid]} | {limited_counts[cid]} |\n"
        
    report += "\n## Limitations\n"
    report += "This list provides a starting point for human annotation but is not exhaustive. The human reviewer retains access to the full frozen corpus to identify missing evidence and must independently verify the actual textual support for each surfaced candidate."
    
    with open(reports_dir / "v3_1_candidate_discovery.md", "w") as f:
        f.write(report)
        
    print(f"Candidate discovery generated: {out_csv}")
    print("Exact candidate count per case:")
    for cid in case_concepts:
        print(f"  {cid}: {discovery_counts[cid]} candidates ({limited_counts[cid]} TITLE_ONLY)")

if __name__ == "__main__":
    main()