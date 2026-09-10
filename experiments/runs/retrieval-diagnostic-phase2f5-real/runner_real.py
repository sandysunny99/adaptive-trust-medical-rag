import json
import csv
from time import perf_counter
from pathlib import Path
from datetime import datetime, timezone
import hashlib

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import HybridRetrievalEngine, Candidate, RRF_K, reciprocal_rank_fusion
from sentence_transformers import SentenceTransformer
from adaptive_trust_medical_rag.retrieval.reranker import CrossEncoderReranker

class RealEmbeddingModel:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)
    def encode(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

def main():
    print("Starting REAL Diagnostic Execution...")
    out_dir = Path("experiments/runs/retrieval-diagnostic-phase2f5-real")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load Corpus
    with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json", "r", encoding="utf-8") as f:
        docs_raw = json.load(f)
        
    corpus = [Candidate(
            chunk_id=d["chunk_id"], document_id=d.get("document_id", d["chunk_id"]),
            text=d.get("text", d.get("abstract", "")),
            source_url=d.get("url", ""), source_authority=d.get("authority_tier", "unknown"),
            metadata=d
        ) for d in docs_raw]

    # 2. Load Adjudicated Labels (V1 Candidates + V2 Screen)
    adjudicated = {}
    cand_csv = Path("experiments/annotations/v3_1_human/pilot/reviewer_workspace/decision_helper_review.csv")
    with open(cand_csv, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["case_id"] not in adjudicated: adjudicated[row["case_id"]] = {}
            adjudicated[row["case_id"]][str(row["document_id"])] = row["human_final_label"]

    queue_csv = Path("experiments/annotations/v3_1_human/pilot/false_negative_screen_v2/human_review_queue.csv")
    with open(queue_csv, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["case_id"] not in adjudicated: adjudicated[row["case_id"]] = {}
            adjudicated[row["case_id"]][str(row["document_id"])] = row["human_final_label"]

    queries = {
        "v3.1h-001": ("How does metformin inhibit hepatic gluconeogenesis?", ["metformin"]),
        "v3.1h-002": ("Clearance pathway for lisinopril", ["lisinopril"]),
        "v3.1h-021": ("Concomitant use of warfarin and aspirin bleeding risk", ["warfarin", "aspirin"]),
        "v3.1h-022": ("CYP2C9 interaction between fluconazole and warfarin", ["fluconazole", "warfarin"]),
        "v3.1h-023": ("Lisinopril and spironolactone interaction hyperkalemia risk", ["lisinopril", "spironolactone"]),
        "v3.1h-046": ("Idiosyncratic drug induced liver injury mechanisms", []),
        "v3.1h-047": ("Risk of hyperkalemia in patients treated with spironolactone", ["spironolactone"]),
        "v3.1h-066": ("Metformin contraindication in severe renal disease", ["metformin"]),
        "v3.1h-067": ("Warfarin target INR monitoring", ["warfarin"]),
        "v3.1h-069": ("Diagnosis of drug induced hepatotoxicity", [])
    }

    print("Loading actual dense encoder (S-PubMedBert-MS-MARCO)...")
    dense_model = RealEmbeddingModel("pritamdeka/S-PubMedBert-MS-MARCO")
    engine = HybridRetrievalEngine(corpus, dense_model, rrf_k=60, top_n=60, top_k=60)

    print("Loading actual cross encoder (MedCPT-Cross-Encoder)...")
    cross_encoder = CrossEncoderReranker("ncbi/MedCPT-Cross-Encoder")

    f0_results = []
    f3_results = []
    candidate_analysis = []
    failures = []

    for cid, (query, q_drugs) in queries.items():
        print(f"Running Case: {cid}...")
        # ACTUALLY execute F0
        bm25_cands = engine.bm25.retrieve(query, top_k=60)
        dense_cands = engine.vector.retrieve(query, top_k=60)
        graph_cands = engine.graph.retrieve(q_drugs, top_k=60) if q_drugs else []
        
        f0_fused = reciprocal_rank_fusion([bm25_cands, dense_cands, graph_cands], k=60, top_n=60)
        
        f0_ranked_ids = [sc.candidate.document_id for sc in f0_fused]
        f0_results.append({
            "query_id": cid, "query": query, "f0_ranked_ids": f0_ranked_ids,
            "top_5": f0_ranked_ids[:5], "top_10": f0_ranked_ids[:10], "top_20": f0_ranked_ids[:20]
        })

        # ACTUALLY execute F3 (MedCPT)
        passages = [sc.candidate.text for sc in f0_fused]
        ce_scores = cross_encoder.score(query, passages) if passages else []
        
        f3_cands = []
        for i, sc in enumerate(f0_fused):
            f3_cands.append({"doc_id": sc.candidate.document_id, "ce_score": ce_scores[i] if i < len(ce_scores) else 0.0})
            
        f3_cands.sort(key=lambda x: x["ce_score"], reverse=True)
        f3_ranked_ids = [c["doc_id"] for c in f3_cands]
        
        f3_results.append({
            "query_id": cid, "query": query, "f3_ranked_ids": f3_ranked_ids,
            "top_5": f3_ranked_ids[:5], "top_10": f3_ranked_ids[:10], "top_20": f3_ranked_ids[:20]
        })
        
        # Post-Retrieval Candidate Analysis (ONLY for adjudicated candidates)
        known_cands = adjudicated.get(cid, {})
        for did, label in known_cands.items():
            f0_rank = f0_ranked_ids.index(did) + 1 if did in f0_ranked_ids else 999
            f3_rank = f3_ranked_ids.index(did) + 1 if did in f3_ranked_ids else 999
            rank_delta = f0_rank - f3_rank
            
            medcpt_score = next((c["ce_score"] for c in f3_cands if c["doc_id"] == did), None)
            
            candidate_analysis.append({
                "query_id": cid, "document_id": did, "human_label": label,
                "f0_rank": f0_rank, "f3_rank": f3_rank,
                "f0_retrieved_at_5": f0_rank <= 5, "f3_retrieved_at_5": f3_rank <= 5,
                "f0_retrieved_at_10": f0_rank <= 10, "f3_retrieved_at_10": f3_rank <= 10,
                "f0_retrieved_at_20": f0_rank <= 20, "f3_retrieved_at_20": f3_rank <= 20,
                "rank_delta": rank_delta, "medcpt_score": medcpt_score
            })
            
            # Analyze Failures based on Actual Empirical Movement
            if label in ["DIRECT_SUPPORT", "PARTIAL_SUPPORT"]:
                if rank_delta > 0: failures.append({"type": "Beneficial Promotion", "cid": cid, "did": did, "desc": f"Promoted relevant evidence by {rank_delta} positions."})
                elif rank_delta < 0: failures.append({"type": "semantic false negative", "cid": cid, "did": did, "desc": f"Demoted relevant evidence by {abs(rank_delta)} positions."})
            elif label in ["NOT_RELEVANT", "NO_EVIDENCE"]:
                if rank_delta > 0: failures.append({"type": "lexical false positive", "cid": cid, "did": did, "desc": f"Promoted unrelated document by {rank_delta} positions."})
                elif rank_delta < 0: failures.append({"type": "Beneficial Demotion", "cid": cid, "did": did, "desc": f"Demoted unrelated document by {abs(rank_delta)} positions."})

    # Save Real Results
    with open(out_dir / "f0_results.jsonl", "w") as f:
        for item in f0_results: f.write(json.dumps(item) + "\n")
    with open(out_dir / "f3_results.jsonl", "w") as f:
        for item in f3_results: f.write(json.dumps(item) + "\n")
    with open(out_dir / "candidate_level_analysis.jsonl", "w") as f:
        for item in candidate_analysis: f.write(json.dumps(item) + "\n")
    with open(out_dir / "failure_taxonomy.json", "w") as f:
        json.dump(failures, f, indent=2)

    print("Real Diagnostic Execution Finished.")
    
if __name__ == '__main__':
    main()
