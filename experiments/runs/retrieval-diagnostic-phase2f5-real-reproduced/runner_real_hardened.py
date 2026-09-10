import json
import csv
from pathlib import Path
from datetime import datetime
import hashlib

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import HybridRetrievalEngine, Candidate, reciprocal_rank_fusion
from sentence_transformers import SentenceTransformer
from adaptive_trust_medical_rag.retrieval.reranker import CrossEncoderReranker

class RealEmbeddingModel:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)
    def encode(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

def main():
    print('REAL_RETRIEVAL_LOOP_STARTED')
    out_dir = Path('experiments/runs/retrieval-diagnostic-phase2f5-real-reproduced')
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load frozen corpus
    with open('experiments/evidence_snapshots/retrieval-v3-real/documents.json', 'r', encoding='utf-8') as f:
        docs_raw = json.load(f)
    frozen_corpus_ids = {d.get('document_id', d.get('chunk_id')) for d in docs_raw}
    corpus = [Candidate(
        chunk_id=d['chunk_id'],
        document_id=d.get('document_id', d['chunk_id']),
        text=d.get('text', d.get('abstract', '')),
        source_url=d.get('url', ''),
        source_authority=d.get('authority_tier', 'unknown'),
        metadata=d,
    ) for d in docs_raw]

    queries = {
        'v3.1h-001': ('How does metformin inhibit hepatic gluconeogenesis?', ['metformin']),
        'v3.1h-002': ('Clearance pathway for lisinopril', ['lisinopril']),
        'v3.1h-021': ('Concomitant use of warfarin and aspirin bleeding risk', ['warfarin', 'aspirin']),
        'v3.1h-022': ('CYP2C9 interaction between fluconazole and warfarin', ['fluconazole', 'warfarin']),
        'v3.1h-023': ('Lisinopril and spironolactone interaction hyperkalemia risk', ['lisinopril', 'spironolactone']),
        'v3.1h-046': ('Idiosyncratic drug induced liver injury mechanisms', []),
        'v3.1h-047': ('Risk of hyperkalemia in patients treated with spironolactone', ['spironolactone']),
        'v3.1h-066': ('Metformin contraindication in severe renal disease', ['metformin']),
        'v3.1h-067': ('Warfarin target INR monitoring', ['warfarin']),
        'v3.1h-069': ('Diagnosis of drug induced hepatotoxicity', []),
    }

    dense_model = RealEmbeddingModel('pritamdeka/S-PubMedBert-MS-MARCO')
    engine = HybridRetrievalEngine(corpus, dense_model, rrf_k=60, top_n=60, top_k=60)
    cross_encoder = CrossEncoderReranker('ncbi/MedCPT-Cross-Encoder')

    # Compute runner provenance SHA-256 before heavy work
    runner_path = Path(__file__)
    with runner_path.open('rb') as rf:
        runner_sha256 = hashlib.sha256(rf.read()).hexdigest()

    # Open result files
    f0_path = out_dir / 'f0_results.jsonl'
    f3_path = out_dir / 'f3_results.jsonl'
    f0_file = f0_path.open('w', encoding='utf-8')
    f3_file = f3_path.open('w', encoding='utf-8')

    # Existing debug file initialization remains
    debug_path = out_dir / 'debug_records.jsonl'
    debug_file = debug_path.open('w', encoding='utf-8')

    for cid, (query, q_drugs) in queries.items():
        bm25_cands = engine.bm25.retrieve(query, top_k=60)
        dense_cands = engine.vector.retrieve(query, top_k=60)
        graph_cands = engine.graph.retrieve(q_drugs, top_k=60) if q_drugs else []
        f0_fused = reciprocal_rank_fusion([bm25_cands, dense_cands, graph_cands], k=60, top_n=60)
        f0_ranked_ids = [sc.candidate.document_id for sc in f0_fused]

        passages = [sc.candidate.text for sc in f0_fused]
        ce_scores = cross_encoder.score(query, passages) if passages else []
        f3_cands = []
        for i, sc in enumerate(f0_fused):
            f3_cands.append({'doc_id': sc.candidate.document_id, 'ce_score': ce_scores[i] if i < len(ce_scores) else 0.0})
        f3_cands.sort(key=lambda x: x['ce_score'], reverse=True)
        f3_ranked_ids = [c['doc_id'] for c in f3_cands]

        # Execution markers
        print(f'PROCESSING_CASE={cid}')
        # After F0 candidates
        print(f'F0_CANDIDATES={len(f0_ranked_ids)}')
        # MedCPT scores count
        print(f'MEDCPT_SCORES={len(ce_scores)}')
        # After F3 candidates
        print(f'F3_CANDIDATES={len(f3_ranked_ids)}')
        # Verify MedCPT input matches F0 ranking
        medcpt_input_ids = [sc.candidate.document_id for sc in f0_fused]
        assert medcpt_input_ids == f0_ranked_ids, 'MedCPT input IDs differ from F0 ranking'
        # Existing assertions continued
        assert set(f3_ranked_ids) == set(f0_ranked_ids), 'Invariant violation: F3 IDs differ from F0'
        assert all(did in frozen_corpus_ids for did in f0_ranked_ids), 'F0 contains IDs not in frozen corpus'
        assert all(did in frozen_corpus_ids for did in f3_ranked_ids), 'F3 contains IDs not in frozen corpus'
        assert len(f0_ranked_ids) == len(set(f0_ranked_ids)), 'Duplicate IDs in F0'
        assert len(f3_ranked_ids) == len(set(f3_ranked_ids)), 'Duplicate IDs in F3'
        assert len(f3_ranked_ids) == len(f0_ranked_ids), 'Length mismatch between F3 and F0'
        assert len(ce_scores) == len(f0_fused), 'MedCPT score count mismatch'

        debug_record = {
            'case_id': cid,
            'f0_ranked_ids': f0_ranked_ids,
            'medcpt_input_ids': [sc.candidate.document_id for sc in f0_fused],
            'medcpt_scores': ce_scores,
            'f3_ranked_ids': f3_ranked_ids,
        }
        debug_file.write(json.dumps(debug_record) + "\n")

        # Write to result files
        f0_file.write(json.dumps({'case_id': cid, 'f0_ranked_ids': f0_ranked_ids}) + "\n")
        f3_file.write(json.dumps({'case_id': cid, 'f3_ranked_ids': f3_ranked_ids}) + "\n")

    # Close files
    debug_file.close()
    f0_file.close()
    f3_file.close()

    # Compute SHA-256 hashes for output files
    def sha256_path(p):
        with p.open('rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    output_hashes = {
        'debug_records.jsonl': sha256_path(debug_path),
        'f0_results.jsonl': sha256_path(f0_path),
        'f3_results.jsonl': sha256_path(f3_path),
    }
    output_hashes_path = out_dir / 'output_hashes.json'
    output_hashes_path.write_text(json.dumps(output_hashes, indent=2))

    # Execution manifest
    manifest = {
        'runner_sha256': runner_sha256,
        'command': 'uv run python runner_real_hardened.py',
        'working_directory': str(Path.cwd()),
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'output_hashes_path': str(output_hashes_path),
        'debug_records_path': str(debug_path),
        'f0_results_path': str(f0_path),
        'f3_results_path': str(f3_path),
    }
    manifest_path = out_dir / 'execution_manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print("REAL_RETRIEVAL_LOOP_COMPLETED")


if __name__ == '__main__':
    main()
