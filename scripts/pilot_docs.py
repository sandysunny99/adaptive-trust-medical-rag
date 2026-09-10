import json

doc_ids = ["41177211", "33048477", "42128628", "42591558", "42374912", "42678243", "42633086"]

with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json", encoding="utf-8") as f:
    docs = {d["document_id"]: d for d in json.load(f)}

with open("scratch/pilot_docs_full.txt", "w", encoding="utf-8") as out:
    for doc_id in doc_ids:
        if doc_id in docs:
            out.write(f"\n--- {doc_id} ---\n")
            out.write(docs[doc_id].get("title", "") + "\n")
            out.write(docs[doc_id].get("abstract", "") + "\n")