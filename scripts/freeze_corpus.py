import json
import hashlib
from pathlib import Path
from datetime import datetime

docs_path = Path("experiments/evidence_snapshots/retrieval-v3-real/documents.json")
with open(docs_path) as f:
    docs = json.load(f)

doc_hash = hashlib.sha256(json.dumps(docs, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

manifest = {
    "corpus_version": "v3.0-real-frozen",
    "document_count": len(docs),
    "source_count": len(set(d.get("url", "") for d in docs)),
    "document_identifiers": [d["document_id"] for d in docs],
    "corpus_sha256": doc_hash,
    "acquisition_timestamp": datetime.utcnow().isoformat() + "Z",
    "c_set_queries": [
        "metformin pharmacology", "warfarin aspirin interaction", "CYP2C9 drug interactions",
        "drug induced liver injury", "spironolactone hyperkalemia", "atorvastatin mechanism of action",
        "lisinopril renal clearance", "omeprazole clopidogrel interaction", "levothyroxine iron interaction",
        "citalopram qt prolongation", "doxorubicin cardiotoxicity", "amiodarone pulmonary toxicity",
        "isotretinoin teratogenicity", "acetaminophen hepatotoxicity", "digoxin toxicity monitoring",
        "alendronate esophageal ulcer", "pantoprazole clopidogrel", "fluoxetine cyp2d6",
        "sertraline pregnancy", "gabapentin sedation", "tramadol seizure risk",
        "celecoxib cardiovascular risk", "rivaroxaban bleeding antidote", "apixaban renal dosing",
        "dabigatran reversal agent"
    ]
}

with open(docs_path.parent / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
    
print("Corpus frozen. SHA-256:", doc_hash)