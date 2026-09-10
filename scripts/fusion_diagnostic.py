import json
from pathlib import Path
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import HybridRetrievalEngine, Candidate

from sentence_transformers import SentenceTransformer

class RealEmbeddingModel:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)
    def encode(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

def main():
    with open("experiments/evidence_snapshots/retrieval-v2_1/documents.json", "r") as f:
        docs_raw = json.load(f)
        
    corpus = []
    for d in docs_raw:
        corpus.append(Candidate(
            chunk_id=d["chunk_id"],
            document_id=d["document_id"],
            text=d.get("text", d.get("abstract", "")),
            source_url=d.get("url", ""),
            source_authority=d.get("authority_tier", "unknown"),
            metadata=d
        ))
        
    with open("experiments/manifests/retrieval_dataset_v2_1.json", "r") as f:
        cases_raw = json.load(f)
        
    model = RealEmbeddingModel("cambridgeltl/SapBERT-from-PubMedBERT-fulltext")
    engine = HybridRetrievalEngine(corpus, model)
    
    print("\n--- RRF Fusion Diagnostic Trace ---\n")
    
    # We will pick a case that succeeds in R1 but fails in R3 (e-01: How does metformin lower blood glucose?)
    target_case = next(c for c in cases_raw if c["case_id"] == "e-12")
    query = target_case["query"]
    expected = set(target_case["expected_document_ids"])
    
    print(f"Case: {target_case['case_id']} | Query: {query}")
    print(f"Expected Documents: {expected}")
    
    # Run individual channels
    bm25_cands = engine.bm25.retrieve(query)
    dense_cands = engine.vector.retrieve(query)
    graph_cands = engine.graph.retrieve(target_case["expected_entity_ids"])
    
    # Build maps
    bm25_ranks = {c.document_id: r+1 for r, (c, s) in enumerate(bm25_cands)}
    dense_ranks = {c.document_id: r+1 for r, (c, s) in enumerate(dense_cands)}
    graph_ranks = {c.document_id: r+1 for r, (c, s) in enumerate(graph_cands)}
    
    fused = engine.retrieve(query, query_drugs=target_case["expected_entity_ids"])
    
    print("\n--- Expected Document Ranks ---")
    for doc_id in expected:
        r_bm25 = bm25_ranks.get(doc_id, float('inf'))
        r_dense = dense_ranks.get(doc_id, float('inf'))
        r_graph = graph_ranks.get(doc_id, float('inf'))
        
        final_rank = next((i+1 for i, sc in enumerate(fused) if sc.candidate.document_id == doc_id), float("inf"))
        final_score = next((sc.rrf_score for i, sc in enumerate(fused) if sc.candidate.document_id == doc_id), 0.0)
        
        print(f"Document: {doc_id}")
        print(f"  Dense Rank: {r_dense}")
        print(f"  BM25 Rank: {r_bm25}")
        print(f"  Graph Rank: {r_graph}")
        print(f"  RRF Score (final): {final_score:.4f} -> Final Rank: {final_rank}")
        
    print("\n--- Top 3 Fused Documents (R3 Output) ---")
    for i in range(min(3, len(fused))):
        c = fused[i].candidate; s = fused[i].rrf_score
        print(f"Rank {i+1}: {c.document_id} (Expected? {c.document_id in expected})")
        print(f"  Dense Rank: {dense_ranks.get(c.document_id, float('inf'))}")
        print(f"  BM25 Rank: {bm25_ranks.get(c.document_id, float('inf'))}")
        print(f"  Graph Rank: {graph_ranks.get(c.document_id, float('inf'))}")
        print(f"  RRF Score: {s:.4f}")

if __name__ == "__main__":
    main()





