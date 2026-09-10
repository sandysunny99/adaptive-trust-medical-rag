import json
from pathlib import Path

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate


def load_real_corpus() -> list[Candidate]:
    manifest_path = Path("data/evidence/manifest.json")
    if not manifest_path.exists():
        return []
    with open(manifest_path, "r") as f:
        data = json.load(f)

    corpus = []
    for doc in data.get("documents", []):
        corpus.append(Candidate(
            chunk_id=doc.get("chunk_id", ""),
            document_id=doc.get("document_id", ""),
            text=doc.get("text", ""),
            source_url=doc.get("source_url", ""),
            source_authority=doc.get("authority_score", 0.5),
            poisoning_score=doc.get("poisoning_score", 0.0),
            metadata={"document_id": doc.get("document_id", ""), "source": doc.get("source", ""), "authority_tier": doc.get("authority_tier", "")}
        ))
    return corpus
