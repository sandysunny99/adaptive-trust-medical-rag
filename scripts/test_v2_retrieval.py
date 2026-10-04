import json
import asyncio
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import HybridRetrievalEngine
from sentence_transformers import SentenceTransformer

class LiveEmbeddingModel:
    def __init__(self, corpus):
        self.corpus = corpus
    def embed_query(self, query: str):
        model = SentenceTransformer("all-MiniLM-L6-v2")
        return model.encode(query).tolist()
    def embed_documents(self, texts):
        return []

def main():
    with open("data/live_medical/LIVE_MEDICAL_CORPUS_V2.json", "r", encoding="utf-8") as f:
        corpus = json.load(f)
    
    engine = HybridRetrievalEngine(corpus, LiveEmbeddingModel(corpus), vector_dim=384, collection_name="medical_evidence_test")
    
    # Query 1: Warfarin and Aspirin
    candidates1 = engine.retrieve("What is the interaction between Warfarin and Aspirin?", ["warfarin", "aspirin"], top_k=3)
    assert any("warfarin" in c.candidate.text.lower() for c in candidates1)
    
    # Query 2: Metformin contraindications
    candidates2 = engine.retrieve("What are the contraindications for Metformin?", ["metformin"], top_k=3)
    assert any("renal" in c.candidate.text.lower() for c in candidates2)
    
    print(f"Retrieval tests passed. Chunk count: {len(corpus)}")

if __name__ == "__main__":
    main()
