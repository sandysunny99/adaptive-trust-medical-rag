import json
import hashlib
from datetime import datetime
from pathlib import Path

def main():
    with open("experiments/evidence_snapshots/retrieval-v2-stageA-provisional/documents.json", "r") as f:
        corpus = json.load(f)
        
    e_set = [
        # E-Set queries (different from C-set)
        # Pharmacology
        {"case_id": "e-01", "query": "How does metformin lower blood glucose?", "tier": "R1", "type": "Pharmacology", "diff": "PARAPHRASE", "c_drug": "metformin", "c_term": ["glucose", "production", "hepatic"]},
        {"case_id": "e-02", "query": "Is atorvastatin's half-life long enough for alternate day dosing?", "tier": "R2", "type": "Pharmacology", "diff": "MECHANISM", "c_drug": "atorvastatin", "c_term": ["half", "life", "pharmacokinetic"]},
        {"case_id": "e-03", "query": "Monitoring requirements for patients on digoxin", "tier": "R2", "type": "Pharmacology", "diff": "SYNONYM", "c_drug": "digoxin", "c_term": ["monitor", "level", "toxicity"]},
        {"case_id": "e-04", "query": "Role of cytochrome P450 2C19 in omeprazole clearance", "tier": "R1", "type": "Pharmacology", "diff": "CYP_DDI", "c_drug": "omeprazole", "c_term": ["cyp2c19", "metabolism", "clearance"]},
        
        # DDI
        {"case_id": "e-05", "query": "Does concomitant aspirin increase bleeding risk in patients receiving warfarin?", "tier": "R3", "type": "DDI", "diff": "PARAPHRASE", "c_drug": "warfarin", "c_term": ["aspirin", "bleed", "hemorrhage"]},
        {"case_id": "e-06", "query": "How does fluconazole alter metabolism mediated by CYP2C9?", "tier": "R2", "type": "DDI", "diff": "CYP_DDI", "c_drug": "fluconazole", "c_term": ["cyp2c9", "inhibit", "metabolism"]},
        {"case_id": "e-07", "query": "Can clopidogrel and omeprazole be safely co-administered?", "tier": "R3", "type": "DDI", "diff": "PARAPHRASE", "c_drug": "clopidogrel", "c_term": ["omeprazole", "interact", "cardiovascular"]},
        {"case_id": "e-08", "query": "Should pantoprazole and calcium carbonate be taken together?", "tier": "R2", "type": "DDI", "diff": "SYNONYM", "c_drug": "pantoprazole", "c_term": ["calcium", "absorp"]},
        {"case_id": "e-09", "query": "Does ferrous sulfate decrease the efficacy of levothyroxine?", "tier": "R2", "type": "DDI", "diff": "PARAPHRASE", "c_drug": "levothyroxine", "c_term": ["iron", "ferrous", "absorp"]},
        
        # ADE
        {"case_id": "e-10", "query": "What potassium-related adverse effect is associated with spironolactone?", "tier": "R3", "type": "ADE", "diff": "PARAPHRASE", "c_drug": "spironolactone", "c_term": ["potassium", "hyperkalemia"]},
        {"case_id": "e-11", "query": "Can paracetamol cause acute hepatic failure?", "tier": "R3", "type": "ADE", "diff": "SYNONYM", "c_drug": "acetaminophen", "c_term": ["liver", "hepatic", "injury", "failure"]},
        {"case_id": "e-12", "query": "Is electrocardiogram monitoring required for citalopram?", "tier": "R2", "type": "ADE", "diff": "MECHANISM", "c_drug": "citalopram", "c_term": ["qt", "qtc", "prolongation", "ecg"]},
        {"case_id": "e-13", "query": "Does amiodarone cause interstitial pneumonitis?", "tier": "R3", "type": "ADE", "diff": "SYNONYM", "c_drug": "amiodarone", "c_term": ["pulmonary", "pneumonitis", "lung"]},
        {"case_id": "e-14", "query": "Heart failure risk following anthracycline therapy", "tier": "R3", "type": "ADE", "diff": "MULTI_ENTITY", "c_drug": "doxorubicin", "c_term": ["cardiotoxicity", "heart failure", "anthracycline"]},
        {"case_id": "e-15", "query": "Risk of esophageal ulceration with Fosamax", "tier": "R2", "type": "ADE", "diff": "SYNONYM", "c_drug": "alendronate", "c_term": ["esophag", "ulcer", "fosamax"]},
        
        # Safety
        {"case_id": "e-16", "query": "Lisinopril dosing in patients with GFR < 30", "tier": "R3", "type": "Medication_Safety", "diff": "PARAPHRASE", "c_drug": "lisinopril", "c_term": ["renal", "kidney", "clearance", "gfr"]},
        {"case_id": "e-17", "query": "Is Accutane contraindicated in females of childbearing potential?", "tier": "R3", "type": "Medication_Safety", "diff": "SYNONYM", "c_drug": "isotretinoin", "c_term": ["pregnan", "teratogen", "accutane"]},
        {"case_id": "e-18", "query": "Use of amoxicillin in patients with IgE-mediated penicillin hypersensitivity", "tier": "R3", "type": "Medication_Safety", "diff": "PARAPHRASE", "c_drug": "amoxicillin", "c_term": ["penicillin", "allerg", "hypersensitivity", "cross"]},
        {"case_id": "e-19", "query": "Antidote for Xarelto-induced major bleeding", "tier": "R3", "type": "Medication_Safety", "diff": "SYNONYM", "c_drug": "rivaroxaban", "c_term": ["andexanet", "reversal", "antidote", "bleed", "xarelto"]}
    ]
    
    cases = []
    
    for q in e_set:
        expected_docs = []
        for doc in corpus:
            text = doc.get("text", doc.get("abstract", "")).lower()
            if q["c_drug"].lower() in text:
                if any(t.lower() in text for t in q["c_term"]):
                    expected_docs.append(doc["document_id"])
                    
        cases.append({
            "case_id": q["case_id"],
            "query": q["query"],
            "risk_tier": q["tier"],
            "claim_type": q["type"],
            "difficulty": q["diff"],
            "expected_document_ids": list(set(expected_docs)),
            "expected_chunk_ids": [f"chunk-{d}-001" for d in set(expected_docs)],
            "expected_entity_ids": [q["c_drug"]],
            "evidence_labels": {"relevant": True, "authority": "Tier 1"} if expected_docs else {}
        })
        
    out_dir = Path("experiments/evidence_snapshots/retrieval-v2_1")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Simple chunking (1 doc = 1 chunk for now, but simulating chunking structure)
    chunks = []
    for doc in corpus:
        doc["chunk_id"] = f"chunk-{doc['document_id']}-001"
        chunks.append(doc)
        
    manifest = {
        "dataset_version": "v2.1",
        "corpus_version": "v2.1",
        "document_count": len(corpus),
        "chunk_count": len(chunks),
        "case_count": len(cases),
        "positive_case_count": sum(1 for c in cases if c["expected_document_ids"]),
        "creation_timestamp": datetime.now().isoformat()
    }
    
    with open(out_dir / "documents.json", "w") as f:
        json.dump(chunks, f, indent=2)
        
    with open("experiments/manifests/retrieval_dataset_v2_1.json", "w") as f:
        json.dump(cases, f, indent=2)
        
    # Hashing
    doc_hash = hashlib.sha256(json.dumps(chunks, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    case_hash = hashlib.sha256(json.dumps(cases, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    manifest["corpus_sha256"] = doc_hash
    manifest["dataset_sha256"] = case_hash
    manifest["ground_truth_sha256"] = case_hash
    
    with open(out_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Generated V2.1: {len(corpus)} docs, {len(cases)} cases ({manifest['positive_case_count']} positive)")

if __name__ == "__main__":
    main()