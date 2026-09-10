import json
import hashlib
from time import perf_counter
from pathlib import Path
from dataclasses import dataclass, field

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import HybridRetrievalEngine, Candidate, RRF_K
from sentence_transformers import SentenceTransformer

class RealEmbeddingModel:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)
    def encode(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

def score_weighted_rrf(bm25_cands, dense_cands, graph_cands, weights, k=RRF_K, top_n=5):
    # weights: dict of w_bm25, w_dense, w_graph
    scored = {}
    
    def add_contrib(ranked, w, channel):
        for rank, (cand, score) in enumerate(ranked, start=1):
            cid = cand.chunk_id
            if cid not in scored:
                scored[cid] = {"cand": cand, "score": 0.0, "bm25_rank": float('inf'), "dense_rank": float('inf'), "graph_rank": float('inf')}
            
            scored[cid]["score"] += w / (k + rank)
            if channel == "bm25": scored[cid]["bm25_rank"] = rank
            elif channel == "dense": scored[cid]["dense_rank"] = rank
            elif channel == "graph": scored[cid]["graph_rank"] = rank

    add_contrib(bm25_cands, weights["w_bm25"], "bm25")
    add_contrib(dense_cands, weights["w_dense"], "dense")
    add_contrib(graph_cands, weights["w_graph"], "graph")
    
    sorted_cands = sorted(scored.values(), key=lambda x: x["score"], reverse=True)
    return sorted_cands[:top_n]

def calc_metrics(fused, expected_ids):
    retrieved = [x["cand"].document_id for x in fused]
    expected = set(expected_ids)
    if not expected: return {"r5": None, "first_rank": None}
    
    r5 = len(set(retrieved[:5]) & expected) / len(expected)
    first_rank = next((i+1 for i, d in enumerate(retrieved) if d in expected), float('inf'))
    
    return {"r5": r5, "first_rank": first_rank}

def main():
    print("Starting Phase 2D Fusion Evaluation...")
    out_dir = Path("experiments/runs/fusion-evaluation-v1")
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
        
    model_name = "pritamdeka/S-PubMedBert-MS-MARCO"
    model = RealEmbeddingModel(model_name)
    engine = HybridRetrievalEngine(corpus, model)
    
    weights_matrix = {
        "F0": {"w_bm25": 1.0, "w_dense": 1.0, "w_graph": 1.0},
        "W1": {"w_bm25": 1.0, "w_dense": 1.5, "w_graph": 1.0},
        "W2": {"w_bm25": 0.75, "w_dense": 1.5, "w_graph": 1.0},
        "W3": {"w_bm25": 1.0, "w_dense": 2.0, "w_graph": 1.0},
    }
    
    manifest = {
        "experiment": "Phase 2D Fusion Evaluation",
        "benchmark": "v2.1",
        "embedding_model": model_name,
        "variants": weights_matrix
    }
    with open("experiments/manifests/fusion_evaluation_v1.json", "w") as f:
        json.dump(manifest, f, indent=2)

    results = []
    
    for case in cases:
        if not case["expected_document_ids"]: continue # Focus only on positive diagnostic cases
        
        q = case["query"]
        expected = case["expected_document_ids"]
        q_drugs = case["expected_entity_ids"]
        
        # Base Channels
        bm25_cands = engine.bm25.retrieve(q)
        dense_cands = engine.vector.retrieve(q)
        graph_cands = engine.graph.retrieve(q_drugs)
        
        # Dense baseline rank
        dense_only_fused = score_weighted_rrf([], dense_cands, [], {"w_bm25":0, "w_dense":1, "w_graph":0})
        dense_metrics = calc_metrics(dense_only_fused, expected)
        dense_rank = dense_metrics["first_rank"]
        
        case_res = {
            "case_id": case["case_id"],
            "difficulty": case["difficulty"],
            "expected": expected,
            "dense_first_rank": dense_rank,
            "fusion": {}
        }
        
        for w_name, w_vals in weights_matrix.items():
            fused = score_weighted_rrf(bm25_cands, dense_cands, graph_cands, w_vals)
            metrics = calc_metrics(fused, expected)
            case_res["fusion"][w_name] = {
                "rank": metrics["first_rank"],
                "r5": metrics["r5"]
            }
            
        results.append(case_res)
        
    with open(out_dir / "inversion_analysis.json", "w") as f:
        json.dump(results, f, indent=2)
        
    # Analyze Inversions
    print("\n--- Fusion Inversion Analysis ---")
    inversions_f0 = [r for r in results if r["dense_first_rank"] <= 5 and r["fusion"]["F0"]["rank"] > 5]
    print(f"F0 (Baseline) Inversions: {len(inversions_f0)}")
    
    for r in inversions_f0:
        print(f"  Case {r['case_id']}: Dense Rank {r['dense_first_rank']} -> F0 Rank {r['fusion']['F0']['rank']}")
        for w_name in ["W1", "W2", "W3"]:
            new_rank = r["fusion"][w_name]["rank"]
            recovered = new_rank <= 5
            print(f"    {w_name}: Rank {new_rank} (Recovered: {recovered})")

if __name__ == "__main__":
    main()