import json

cases = [
    ("v3.1h-001", ["metformin", "hepatic", "glucose"]),
    ("v3.1h-002", ["lisinopril", "clearance", "renal"]),
    ("v3.1h-021", ["warfarin", "aspirin", "bleeding"]),
    ("v3.1h-022", ["fluconazole", "warfarin"]),
    ("v3.1h-023", ["spironolactone", "lisinopril"]),
    ("v3.1h-046", ["liver", "injury"]),
    ("v3.1h-047", ["spironolactone", "hyperkalemia"]),
    ("v3.1h-066", ["metformin", "renal"]),
    ("v3.1h-067", ["warfarin", "inr"]),
    ("v3.1h-069", ["hepatotoxicity"])
]

with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json") as f:
    docs = json.load(f)

for case_id, terms in cases:
    print(f"\n--- {case_id} ---")
    for doc in docs:
        text = doc.get("abstract", "").lower()
        if any(term in text for term in terms): # simple OR to find candidates
            # Check if all terms are present for stronger candidates
            if all(term in text for term in terms):
                print(f"STRONG CANDIDATE: {doc['document_id']}")
                print(doc.get("abstract", "")[:500])