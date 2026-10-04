import sys, json, os
sys.path.insert(0, 'src')
from adaptive_trust_medical_rag.evaluation.live_variants import SimpleEmbeddingModel
from sentence_transformers import SentenceTransformer
import warnings
warnings.filterwarnings('ignore')

def main():
    queries = [
        "statin therapy is common",
        "Does statin interact with aspirin?",
        "Statin is a drug. Cyanide is a poison."
    ]

    print("Loading models...")
    simple_model = SimpleEmbeddingModel()
    real_model = SentenceTransformer("pritamdeka/S-PubMedBert-MS-MARCO")

    results = []
    
    for q in queries:
        simple_vec = simple_model.encode([q])[0]
        real_vec = real_model.encode([q], normalize_embeddings=True)[0]
        
        results.append({
            "query": q,
            "SimpleEmbeddingModel": {
                "vector_dimension": len(simple_vec),
                "nonzero_dimensions": sum(1 for v in simple_vec if v > 0),
                "is_zero_vector": all(v == 0.0 for v in simple_vec)
            },
            "S-PubMedBert-MS-MARCO": {
                "vector_dimension": len(real_vec),
                "nonzero_dimensions": sum(1 for v in real_vec if abs(v) > 1e-6),
                "is_zero_vector": all(v == 0.0 for v in real_vec)
            },
            "evidence_source": "runtime_capture"
        })
        
    out_dir = "experiments/track_a_abstract_enriched_reannotation_v1/baseline_model_authorization_v4"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/MODEL_CHARACTERIZATION_RUNTIME.jsonl", "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print("Done")

if __name__ == "__main__":
    main()
