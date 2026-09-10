import json
import hashlib
from time import perf_counter
from pathlib import Path

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import HybridRetrievalEngine, Candidate, RRF_K
from sentence_transformers import SentenceTransformer
from adaptive_trust_medical_rag.retrieval.reranker import CrossEncoderReranker

class RealEmbeddingModel:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)
    def encode(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

def score_rrf(bm25_cands, dense_cands, graph_cands, k=RRF_K, top_n=20):
    scored = {}
    
    def add_contrib(ranked, channel):
        for rank, (cand, score) in enumerate(ranked, start=1):
            cid = cand.chunk_id
            if cid not in scored:
                scored[cid] = {"cand": cand, "score": 0.0, "bm25_rank": float('inf'), "dense_rank": float('inf'), "graph_rank": float('inf')}
            
            scored[cid]["score"] += 1.0 / (k + rank)
            if channel == "bm25": scored[cid]["bm25_rank"] = rank
            elif channel == "dense": scored[cid]["dense_rank"] = rank
            elif channel == "graph": scored[cid]["graph_rank"] = rank

    add_contrib(bm25_cands, "bm25")
    add_contrib(dense_cands, "dense")
    add_contrib(graph_cands, "graph")
    
    sorted_cands = sorted(scored.values(), key=lambda x: x["score"], reverse=True)
    return sorted_cands[:top_n]

def calc_metrics(fused, expected_ids, top_n=5):
    retrieved = [x["cand"].document_id for x in fused]
    expected = set(expected_ids)
    if not expected: return {"r5": None, "first_rank": None, "mrr": None}
    
    r5 = len(set(retrieved[:top_n]) & expected) / len(expected)
    first_rank = next((i+1 for i, d in enumerate(retrieved) if d in expected), float('inf'))
    mrr = 1.0 / first_rank if first_rank <= top_n else 0.0
    
    return {"r5": r5, "first_rank": first_rank, "mrr": mrr}

def main():
    print("Starting Phase 2E Biomedical Reranker Evaluation...")
    out_dir = Path("experiments/runs/fusion-evaluation-v3")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    with open("experiments/evidence_snapshots/retrieval-v2_1/documents.json", "r") as f:
        docs_raw = json.load(f)
        
    corpus = [Candidate(
            chunk_id=d["chunk_id"], document_id=d["document_id"],
            text=d.get("text", d.get("abstract", "")),
            source_url=d.get("url", ""), source_authority=d.get("authority_tier", "unknown"),
            metadata=d
        ) for d in docs_raw]
        
    with open("experiments/manifests/retrieval_dataset_v2_1.json", "r") as f:
        cases = json.load(f)
        
    dense_model_name = "pritamdeka/S-PubMedBert-MS-MARCO"
    cross_model_name = "ncbi/MedCPT-Cross-Encoder"
    
    print(f"Loading dense encoder: {dense_model_name}...")
    dense_model = RealEmbeddingModel(dense_model_name)
    engine = HybridRetrievalEngine(corpus, dense_model)
    
    print(f"Loading cross encoder: {cross_model_name}...")
    cross_encoder = CrossEncoderReranker(cross_model_name)
    
    manifest = {
        "experiment": "Phase 2E Biomedical Reranker Evaluation",
        "benchmark": "v2.1",
        "embedding_model": dense_model_name,
        "cross_encoder_model": cross_model_name,
        "candidate_pool_size": 20
    }
    with open("experiments/manifests/fusion_evaluation_v3.json", "w") as f:
        json.dump(manifest, f, indent=2)

    results = []
    recovered_count = 0
    regression_count = 0
    
    for case in cases:
        if not case["expected_document_ids"]: continue
        
        q = case["query"]
        expected = case["expected_document_ids"]
        q_drugs = case["expected_entity_ids"]
        
        t0 = perf_counter()
        
        # Base Channels
        bm25_cands = engine.bm25.retrieve(q)
        dense_cands = engine.vector.retrieve(q)
        graph_cands = engine.graph.retrieve(q_drugs)
        
        pool_gen_ms = (perf_counter() - t0) * 1000
        
        # F0: RRF Top 20
        f0_fused = score_rrf(bm25_cands, dense_cands, graph_cands, top_n=20)
        f0_metrics = calc_metrics(f0_fused, expected)
        f0_rank = f0_metrics["first_rank"]
        
        # F3: Cross-Encoder Reranking
        t1 = perf_counter()
        passages = [c["cand"].text for c in f0_fused]
        scores = cross_encoder.score(q, passages) if passages else []
        
        f3_cands = []
        for i, c in enumerate(f0_fused):
            new_c = c.copy()
            new_c["ce_score"] = scores[i]
            f3_cands.append(new_c)
        f3_cands.sort(key=lambda x: x["ce_score"], reverse=True)
            
        ce_ms = (perf_counter() - t1) * 1000
        total_ms = pool_gen_ms + ce_ms
            
        f3_metrics = calc_metrics(f3_cands, expected)
        f3_rank = f3_metrics["first_rank"]
        
        if f0_rank > 5 and f3_rank <= 5: recovered_count += 1
        if f0_rank <= 5 and f3_rank > 5: regression_count += 1
        
        case_res = {
            "case_id": case["case_id"],
            "embedding_model": "E1",
            "candidate_pool_size": 20,
            "reranker_model": cross_model_name,
            "f0_top_n": [x["cand"].document_id for x in f0_fused[:20]],
            "f3_top_n": [x["cand"].document_id for x in f3_cands[:20]],
            "expected_document_ids": expected,
            "f0_first_relevant_rank": f0_rank,
            "f3_first_relevant_rank": f3_rank,
            "f0_recall_at_5": f0_metrics["r5"],
            "f3_recall_at_5": f3_metrics["r5"],
            "f0_mrr": f0_metrics["mrr"],
            "f3_mrr": f3_metrics["mrr"],
            "f3_scores": [x["ce_score"] for x in f3_cands[:5]] if f3_cands else [],
            "latency_ms": {"pool_generation": pool_gen_ms, "reranker": ce_ms, "total": total_ms}
        }
            
        results.append(case_res)
        
    with open(out_dir / "case_results.jsonl", "w") as f:
        for r in results: f.write(json.dumps(r) + "\n")
        
    print("\n--- Biomedical F3 Diagnostic ---")
    print(f"Total Positive Cases: {len(results)}")
    
    pool_recall_count = sum(1 for r in results if r["f0_first_relevant_rank"] <= 20)
    print(f"Candidate-Pool Recall@20: {pool_recall_count}/{len(results)}")
    
    print(f"Recovered (F0>5 -> F3<=5): {recovered_count}")
    print(f"Regressions (F0<=5 -> F3>5): {regression_count}")

if __name__ == "__main__":
    main()