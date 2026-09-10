import json
with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json", "r", encoding="utf-8") as f:
    docs = json.load(f)
print(f"Total docs: {len(docs)}")
print(f"First doc keys: {docs[0].keys()}")