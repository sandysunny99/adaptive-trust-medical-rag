import json

cases = {
    "v3.1h-001": ["metformin", "hepatic", "glucose"],
    "v3.1h-002": ["lisinopril", "clearance"],
    "v3.1h-021": ["warfarin", "aspirin"],
    "v3.1h-022": ["fluconazole", "warfarin"],
    "v3.1h-023": ["spironolactone", "lisinopril"],
    "v3.1h-046": ["liver", "injury", "mechanism"],
    "v3.1h-047": ["spironolactone", "hyperkalemia"],
    "v3.1h-066": ["metformin", "renal"],
    "v3.1h-067": ["warfarin", "inr"],
    "v3.1h-069": ["hepatotoxicity"]
}

with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json", encoding="utf-8") as f:
    docs = json.load(f)

with open("scratch/pilot_candidates.txt", "w", encoding="utf-8") as out:
    for case_id, terms in cases.items():
        out.write(f"\n--- {case_id} ---\n")
        found = 0
        for doc in docs:
            text = doc.get("abstract", "")
            if terms[0] in text.lower():
                out.write(f"[{doc['document_id']}] {text}\n")
                found += 1
                if found > 5: break