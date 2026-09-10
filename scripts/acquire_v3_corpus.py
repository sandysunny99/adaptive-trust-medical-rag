import json
import time
from pathlib import Path
from datetime import datetime
from adaptive_trust_medical_rag.evidence_sources.pubmed_adapter import PubMedAdapter, AdapterExecutionMode

def main():
    print("Acquiring V3 Real Corpus...")
    out_dir = Path("experiments/evidence_snapshots/retrieval-v3-real")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    c_set = [
        "metformin pharmacology",
        "warfarin aspirin interaction",
        "CYP2C9 drug interactions",
        "drug induced liver injury",
        "spironolactone hyperkalemia",
        "atorvastatin mechanism of action",
        "lisinopril renal clearance",
        "omeprazole clopidogrel interaction",
        "levothyroxine iron interaction",
        "citalopram qt prolongation",
        "doxorubicin cardiotoxicity",
        "amiodarone pulmonary toxicity",
        "isotretinoin teratogenicity",
        "acetaminophen hepatotoxicity",
        "digoxin toxicity monitoring",
        "alendronate esophageal ulcer",
        "pantoprazole clopidogrel",
        "fluoxetine cyp2d6",
        "sertraline pregnancy",
        "gabapentin sedation",
        "tramadol seizure risk",
        "celecoxib cardiovascular risk",
        "rivaroxaban bleeding antidote",
        "apixaban renal dosing",
        "dabigatran reversal agent"
    ]
    
    adapter = PubMedAdapter()
    adapter.mode = AdapterExecutionMode.LIVE_API_MODE
    
    corpus_docs = []
    seen_ids = set()
    
    print(f"Executing {len(c_set)} C-SET queries...")
    for q in c_set:
        print(f"  Searching: {q}")
        res = adapter.search(q, limit=10)
        
        for r in res:
            pmid = r["source_id"]
            if pmid not in seen_ids:
                seen_ids.add(pmid)
                doc = adapter.fetch(pmid)
                norm = adapter.normalize(doc)
                if norm and (norm.get("abstract") or norm.get("title")):
                    norm["document_id"] = norm["source_id"]
                    norm["text"] = norm.get("abstract", norm.get("title", ""))
                    norm["authority_tier"] = "PubMed_Central"
                    corpus_docs.append(norm)
        time.sleep(1.0)
        
    print(f"Acquired {len(corpus_docs)} real documents.")
    
    chunks = []
    for doc in corpus_docs:
        doc["chunk_id"] = f"chunk-{doc['document_id']}-001"
        chunks.append(doc)
        
    with open(out_dir / "documents.json", "w") as f:
        json.dump(chunks, f, indent=2)
        
    print("Saved documents to experiments/evidence_snapshots/retrieval-v3-real/documents.json")

if __name__ == "__main__":
    main()