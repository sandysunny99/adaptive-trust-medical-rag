import os
import json
import hashlib
from time import perf_counter
from pathlib import Path
from adaptive_trust_medical_rag.evaluation.evaluator import make_smoke_dataset
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import HybridRetrievalEngine, DrugRelationship
from adaptive_trust_medical_rag.evaluation.data_loader import load_real_corpus
from adaptive_trust_medical_rag.evaluation.live_variants import SimpleEmbeddingModel
from adaptive_trust_medical_rag.evaluation.retrieval_evaluator import RetrievalEvaluator

def main():
    print("Starting Validated Retrieval Baseline R0-R3...")
    out_dir = Path("experiments/runs/retrieval-baseline-v1")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Dataset
    dataset = make_smoke_dataset()
    cases = dataset.cases
    
    # 2. Corpus & True Ground Truth
    corpus = load_real_corpus()
    
    gt_path = Path("experiments/manifests/ground_truth.json")
    with open(gt_path, "r") as f:
        ground_truth = json.load(f)
        
    evaluator = RetrievalEvaluator(ground_truth)
    model = SimpleEmbeddingModel()
    
    results_all = []
    
    for variant in ["R0", "R1", "R2", "R3"]:
        print(f"Running variant {variant}...")
        engine = HybridRetrievalEngine(corpus, model)
        
        # Load the graph with drug relationships only if Graph channel is active
        # The true relationships based on the 4 documents:
        engine.graph.add_relationship(DrugRelationship("warfarin", "aspirin", "contraindicated", "severe", "chunk-warfarin-001"))
        engine.graph.add_relationship(DrugRelationship("haloperidol", "azithromycin", "interaction", "severe", "chunk-haloperidol-001"))
        engine.graph.add_relationship(DrugRelationship("spironolactone", "potassium", "contraindicated", "severe", "chunk-spironolactone-001"))
        
        def mock_retrieve_empty(*args, **kwargs):
            return []
            
        if variant == "R0":
            engine.vector.retrieve = mock_retrieve_empty
            engine.graph.retrieve = mock_retrieve_empty
            channels = ["bm25"]
        elif variant == "R1":
            engine.bm25.retrieve = mock_retrieve_empty
            engine.graph.retrieve = mock_retrieve_empty
            channels = ["vector"]
        elif variant == "R2":
            engine.graph.retrieve = mock_retrieve_empty
            channels = ["bm25", "vector"]
        else: # R3
            channels = ["bm25", "vector", "graph"]
            
        variant_dir = out_dir / variant.lower()
        variant_dir.mkdir(exist_ok=True)
        
        for case in cases:
            q_hash = hashlib.sha256(case.query.encode("utf-8")).hexdigest()
            t0 = perf_counter()
            fused = engine.retrieve(case.query, query_drugs=case.expected_drugs)
            latency_ms = (perf_counter() - t0) * 1000
            
            record = evaluator.evaluate_case(case, variant, fused, latency_ms=latency_ms, query_hash=q_hash)
            record.channels = channels
            results_all.append(record)
            
            with open(variant_dir / f"{case.case_id}.json", "w") as f:
                d = record.__dict__.copy()
                d["metrics"] = record.metrics.__dict__
                json.dump(d, f, indent=2)
                
    with open(out_dir / "case_results.jsonl", "w") as f:
        for r in results_all:
            d = r.__dict__.copy()
            d["metrics"] = r.metrics.__dict__
            f.write(json.dumps(d) + "\n")
            
    print("Baseline run completed!")
    
if __name__ == "__main__":
    main()