import json
import time
import hashlib
import re
from datetime import datetime
from pathlib import Path

from adaptive_trust_medical_rag.evidence_sources.pubmed_adapter import PubMedAdapter
from adaptive_trust_medical_rag.evidence_sources.europepmc_adapter import EuropePMCAdapter
from adaptive_trust_medical_rag.evidence_sources.openfda_adapter import OpenFDAAdapter

def main():
    queries = [
        {"case_id": "q-01", "query": "mechanism of action of metformin", "tier": "R1", "type": "Pharmacology", "diff": "EASY_EXACT", "drugs": ["metformin"], "src": "pubmed"},
        {"case_id": "q-02", "query": "warfarin interaction with aspirin", "tier": "R3", "type": "DDI", "diff": "EASY_EXACT", "drugs": ["warfarin", "aspirin"], "src": "pubmed"},
        {"case_id": "q-03", "query": "hyperkalemia spironolactone", "tier": "R3", "type": "ADE", "diff": "EASY_EXACT", "drugs": ["spironolactone"], "src": "pubmed"},
        {"case_id": "q-04", "query": "CYP2C9 inhibition by fluconazole", "tier": "R2", "type": "DDI", "diff": "CYP_DDI", "drugs": ["fluconazole"], "src": "pubmed"},
        {"case_id": "q-05", "query": "drug-induced liver injury acetaminophen", "tier": "R3", "type": "ADE", "diff": "PARAPHRASE", "drugs": ["acetaminophen"], "src": "openfda"},
        {"case_id": "q-06", "query": "atorvastatin pharmacokinetics", "tier": "R1", "type": "Pharmacology", "diff": "EASY_EXACT", "drugs": ["atorvastatin"], "src": "pubmed"},
        {"case_id": "q-07", "query": "lisinopril renal impairment dose adjustment", "tier": "R2", "type": "Medication_Safety", "diff": "HIGH_RISK_SAFETY", "drugs": ["lisinopril"], "src": "openfda"},
        {"case_id": "q-08", "query": "omeprazole CYP2C19", "tier": "R1", "type": "Pharmacology", "diff": "MECHANISM", "drugs": ["omeprazole"], "src": "pubmed"},
        {"case_id": "q-09", "query": "amoxicillin contraindication penicillin allergy", "tier": "R3", "type": "Medication_Safety", "diff": "EASY_EXACT", "drugs": ["amoxicillin", "penicillin"], "src": "pubmed"},
        {"case_id": "q-10", "query": "sertraline serotonin syndrome risk", "tier": "R3", "type": "ADE", "diff": "HIGH_RISK_SAFETY", "drugs": ["sertraline"], "src": "pubmed"},
        {"case_id": "q-11", "query": "citalopram QTc prolongation", "tier": "R2", "type": "ADE", "diff": "EASY_EXACT", "drugs": ["citalopram"], "src": "pubmed"},
        {"case_id": "q-12", "query": "gabapentin withdrawal seizures", "tier": "R3", "type": "ADE", "diff": "HIGH_RISK_SAFETY", "drugs": ["gabapentin"], "src": "pubmed"},
        {"case_id": "q-13", "query": "clopidogrel omeprazole interaction", "tier": "R2", "type": "DDI", "diff": "EASY_EXACT", "drugs": ["clopidogrel", "omeprazole"], "src": "pubmed"},
        {"case_id": "q-14", "query": "lithium toxicity dehydration", "tier": "R3", "type": "Medication_Safety", "diff": "HIGH_RISK_SAFETY", "drugs": ["lithium"], "src": "pubmed"},
        {"case_id": "q-15", "query": "levothyroxine absorption iron", "tier": "R1", "type": "DDI", "diff": "MECHANISM", "drugs": ["levothyroxine", "iron"], "src": "pubmed"},
        {"case_id": "q-16", "query": "rivaroxaban reversal agent", "tier": "R3", "type": "Medication_Safety", "diff": "HIGH_RISK_SAFETY", "drugs": ["rivaroxaban"], "src": "pubmed"},
        {"case_id": "q-17", "query": "methotrexate toxicity folic acid", "tier": "R2", "type": "ADE", "diff": "EASY_EXACT", "drugs": ["methotrexate", "folic acid"], "src": "pubmed"},
        {"case_id": "q-18", "query": "azithromycin cardiovascular death", "tier": "R3", "type": "ADE", "diff": "HIGH_RISK_SAFETY", "drugs": ["azithromycin"], "src": "pubmed"},
        {"case_id": "q-19", "query": "digoxin therapeutic range", "tier": "R1", "type": "Pharmacology", "diff": "EASY_EXACT", "drugs": ["digoxin"], "src": "pubmed"},
        {"case_id": "q-20", "query": "valproic acid teratogenicity pregnancy", "tier": "R3", "type": "Medication_Safety", "diff": "HIGH_RISK_SAFETY", "drugs": ["valproic acid"], "src": "pubmed"},
        {"case_id": "q-21", "query": "ciprofloxacin tendon rupture", "tier": "R2", "type": "ADE", "diff": "EASY_EXACT", "drugs": ["ciprofloxacin"], "src": "openfda"},
        {"case_id": "q-22", "query": "isotretinoin pregnancy prevention", "tier": "R3", "type": "Medication_Safety", "diff": "HIGH_RISK_SAFETY", "drugs": ["isotretinoin"], "src": "openfda"},
        {"case_id": "q-23", "query": "doxorubicin cardiotoxicity", "tier": "R3", "type": "ADE", "diff": "EASY_EXACT", "drugs": ["doxorubicin"], "src": "pubmed"},
        {"case_id": "q-24", "query": "tramadol seizure threshold", "tier": "R2", "type": "ADE", "diff": "MECHANISM", "drugs": ["tramadol"], "src": "pubmed"},
        {"case_id": "q-25", "query": "linezolid MAOI interaction", "tier": "R3", "type": "DDI", "diff": "HIGH_RISK_SAFETY", "drugs": ["linezolid", "MAOI"], "src": "pubmed"},
        {"case_id": "q-26", "query": "amiodarone pulmonary toxicity", "tier": "R3", "type": "ADE", "diff": "EASY_EXACT", "drugs": ["amiodarone"], "src": "pubmed"},
        {"case_id": "q-27", "query": "pantoprazole absorption calcium", "tier": "R1", "type": "DDI", "diff": "MECHANISM", "drugs": ["pantoprazole", "calcium"], "src": "pubmed"},
        {"case_id": "q-28", "query": "trazodone priapism", "tier": "R2", "type": "ADE", "diff": "EASY_EXACT", "drugs": ["trazodone"], "src": "pubmed"},
        {"case_id": "q-29", "query": "alendronate esophagitis", "tier": "R2", "type": "ADE", "diff": "EASY_EXACT", "drugs": ["alendronate"], "src": "pubmed"},
        {"case_id": "q-30", "query": "metronidazole disulfiram-like reaction", "tier": "R2", "type": "DDI", "diff": "EASY_EXACT", "drugs": ["metronidazole"], "src": "pubmed"}
    ]
    
    pubmed = PubMedAdapter()
    fda = OpenFDAAdapter()
    europepmc = EuropePMCAdapter()
    
    docs_by_id = {}
    cases = []
    
    for q in queries:
        try:
            adapter = pubmed if q["src"] == "pubmed" else (fda if q["src"] == "openfda" else europepmc)
            results = adapter.search(q["query"], limit=3)
            norm = []
            if q["src"] == "pubmed":
                for r in results:
                    f = adapter.fetch(r["source_id"])
                    if f: norm.append(adapter.normalize(f))
            elif q["src"] == "openfda":
                for r in results:
                    f = adapter.fetch(r.get("id", r.get("application_number", "")))
                    if f: norm.append(adapter.normalize(f))
            else:
                for r in results:
                    f = adapter.fetch(r.get("pmid", r.get("id", "")))
                    if f: norm.append(adapter.normalize(f))
                
            expected_docs = []
            for n in norm:
                doc_id = n.get("document_id", n.get("source_id", "unknown"))
                n["document_id"] = doc_id
                
                # Make sure "text" exists
                if "text" not in n:
                    n["text"] = n.get("abstract", n.get("title", ""))
                    
                if doc_id not in docs_by_id:
                    chunk_id = f"chunk-{doc_id}-001"
                    n["chunk_id"] = chunk_id
                    docs_by_id[doc_id] = n
                else:
                    chunk_id = docs_by_id[doc_id]["chunk_id"]
                    
                text_lower = n["text"].lower()
                relevant = all(d.lower() in text_lower for d in q["drugs"])
                
                if relevant:
                    expected_docs.append(doc_id)
                    
            cases.append({
                "case_id": q["case_id"],
                "query": q["query"],
                "risk_tier": q["tier"],
                "claim_type": q["type"],
                "difficulty": q["diff"],
                "expected_document_ids": list(set(expected_docs)),
                "expected_chunk_ids": [f"chunk-{d}-001" for d in set(expected_docs)],
                "expected_entity_ids": q["drugs"],
                "expected_source_types": [docs_by_id[d].get("source", docs_by_id[d].get("source_type", "unknown")) for d in set(expected_docs)],
                "evidence_labels": {"relevant": True, "authority": "Tier 1"} if expected_docs else {}
            })
        except Exception as e:
            pass
            
    out_dir = Path("experiments/evidence_snapshots/retrieval-v2")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    docs_list = list(docs_by_id.values())
    manifest = {
        "dataset_version": "v2",
        "corpus_version": "v2",
        "document_count": len(docs_list),
        "chunk_count": len(docs_list),
        "case_count": len(cases),
        "positive_case_count": sum(1 for c in cases if c["expected_document_ids"]),
        "creation_timestamp": datetime.now().isoformat()
    }
    
    with open(out_dir / "documents.json", "w") as f:
        json.dump(docs_list, f, indent=2)
    with open(out_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    with open("experiments/manifests/retrieval_dataset_v2.json", "w") as f:
        json.dump(cases, f, indent=2)
        
    print(f"Acquired {len(docs_list)} documents for {len(cases)} cases.")
    print(f"Positive cases: {manifest['positive_case_count']}")
    
if __name__ == "__main__":
    main()