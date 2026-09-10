import json
import time
import hashlib
from datetime import datetime
from pathlib import Path

from adaptive_trust_medical_rag.evidence_sources.pubmed_adapter import PubMedAdapter
from adaptive_trust_medical_rag.evidence_sources.europepmc_adapter import EuropePMCAdapter
from adaptive_trust_medical_rag.evidence_sources.openfda_adapter import OpenFDAAdapter

def main():
    # CORPUS ACQUISITION QUERIES (C-set)
    # These are used strictly to build the corpus, NOT for evaluation.
    c_set = [
        # Pharmacology
        {"q": "metformin mechanisms", "src": "pubmed", "limit": 4},
        {"q": "atorvastatin pharmacokinetics half life", "src": "pubmed", "limit": 3},
        {"q": "digoxin therapeutic index monitoring", "src": "pubmed", "limit": 3},
        {"q": "omeprazole CYP2C19 metabolism", "src": "europepmc", "limit": 3},
        
        # DDI
        {"q": "warfarin aspirin interaction bleeding", "src": "openfda", "limit": 3},
        {"q": "fluconazole CYP2C9 inhibition", "src": "pubmed", "limit": 4},
        {"q": "clopidogrel omeprazole cardiovascular", "src": "pubmed", "limit": 3},
        {"q": "pantoprazole calcium absorption", "src": "pubmed", "limit": 2},
        {"q": "levothyroxine iron absorption", "src": "pubmed", "limit": 2},
        
        # ADE
        {"q": "spironolactone hyperkalemia risk", "src": "pubmed", "limit": 3},
        {"q": "acetaminophen drug induced liver injury", "src": "openfda", "limit": 3},
        {"q": "citalopram QTc prolongation", "src": "pubmed", "limit": 3},
        {"q": "amiodarone pulmonary toxicity", "src": "pubmed", "limit": 2},
        {"q": "doxorubicin cardiotoxicity", "src": "pubmed", "limit": 2},
        {"q": "alendronate esophagitis", "src": "openfda", "limit": 2},
        
        # Safety
        {"q": "lisinopril renal impairment dosing", "src": "openfda", "limit": 3},
        {"q": "isotretinoin teratogenicity pregnancy", "src": "openfda", "limit": 3},
        {"q": "amoxicillin penicillin allergy cross reactivity", "src": "pubmed", "limit": 2},
        {"q": "rivaroxaban andexanet alfa reversal", "src": "pubmed", "limit": 2}
    ]
    
    pubmed = PubMedAdapter()
    fda = OpenFDAAdapter()
    europepmc = EuropePMCAdapter()
    
    docs_by_id = {}
    
    print("Fetching Corpus (C-Set)...")
    for item in c_set:
        try:
            adapter = pubmed if item["src"] == "pubmed" else (fda if item["src"] == "openfda" else europepmc)
            results = adapter.search(item["q"], limit=item["limit"])
            norm = []
            
            if item["src"] == "pubmed":
                for r in results:
                    f = adapter.fetch(r["source_id"])
                    if f: norm.append(adapter.normalize(f))
            elif item["src"] == "openfda":
                for r in results:
                    f = adapter.fetch(r.get("id", r.get("application_number", "")))
                    if f: norm.append(adapter.normalize(f))
            else:
                for r in results:
                    f = adapter.fetch(r.get("pmid", r.get("id", "")))
                    if f: norm.append(adapter.normalize(f))
                    
            for n in norm:
                doc_id = n.get("document_id", n.get("source_id", "unknown"))
                n["document_id"] = doc_id
                
                if "text" not in n:
                    n["text"] = n.get("abstract", n.get("title", ""))
                    
                if doc_id not in docs_by_id:
                    # Simple 1:1 chunk mapping for now, to be improved in proper chunking pass
                    chunk_id = f"chunk-{doc_id}-001"
                    n["chunk_id"] = chunk_id
                    docs_by_id[doc_id] = n
                    
        except Exception as e:
            pass
        time.sleep(0.5)

    docs_list = list(docs_by_id.values())
    
    # Write frozen corpus
    out_dir = Path("experiments/evidence_snapshots/retrieval-v2_1")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "documents.json", "w") as f:
        json.dump(docs_list, f, indent=2)
        
    print(f"Frozen {len(docs_list)} documents in V2.1 Corpus.")

if __name__ == "__main__":
    main()