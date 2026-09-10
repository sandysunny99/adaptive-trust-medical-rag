import os
import json
import hashlib
from time import perf_counter
from pathlib import Path
from dataclasses import dataclass

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import HybridRetrievalEngine, DrugRelationship, Candidate
from adaptive_trust_medical_rag.evaluation.live_variants import SimpleEmbeddingModel
from adaptive_trust_medical_rag.evaluation.retrieval_evaluator import RetrievalEvaluator

@dataclass
class EvalCase:
    case_id: str
    query: str
    expected_docs: list[str]

def main():
    print("Starting Validated Retrieval Baseline v2.1 (R0-R3)...")
    out_dir = Path("experiments/runs/retrieval-baseline-v2_1")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Load Corpus
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
        
    # Load Cases
    with open("experiments/manifests/retrieval_dataset_v2_1.json", "r") as f:
        cases_raw = json.load(f)
        
    cases = []
    for c in cases_raw:
        cases.append(c)
        
    evaluator = RetrievalEvaluator({c["case_id"]: c for c in cases_raw})
    model = SimpleEmbeddingModel()
    
    results_all = []
    
    class MockCase:
        def __init__(self, c):
            self.case_id = c["case_id"]
            self.query = c["query"]
            self.expected_docs = c["expected_document_ids"]
            self.risk_tier = c["risk_tier"]
            self.claim_type = c["claim_type"]
    
    for variant in ["R0", "R1", "R2", "R3"]:
        print(f"Running variant {variant}...")
        engine = HybridRetrievalEngine(corpus, model)
        
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
        else:
            channels = ["bm25", "vector", "graph"]
            
        variant_dir = out_dir / variant.lower()
        variant_dir.mkdir(exist_ok=True)
        
        for case in cases:
            q_hash = hashlib.sha256(case["query"].encode("utf-8")).hexdigest()
            t0 = perf_counter()
            fused = engine.retrieve(case["query"], query_drugs=case["expected_entity_ids"])
            latency_ms = (perf_counter() - t0) * 1000
            
            mock_case = MockCase(case)
            record = evaluator.evaluate_case(mock_case, variant, fused, latency_ms=latency_ms, query_hash=q_hash)
            record.channels = channels
            
            results_all.append(record)
            
            with open(variant_dir / f"{case['case_id']}.json", "w") as f:
                d = record.__dict__.copy()
                d["metrics"] = record.metrics.__dict__
                json.dump(d, f, indent=2)
                
    with open(out_dir / "case_results.jsonl", "w") as f:
        for r in results_all:
            d = r.__dict__.copy()
            d["metrics"] = r.metrics.__dict__
            f.write(json.dumps(d) + "\n")
            
    print("V2.1 Baseline run completed!")
    
if __name__ == "__main__":
    main()