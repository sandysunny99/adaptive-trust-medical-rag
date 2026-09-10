import json
import hashlib
from pathlib import Path

def get_hash(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()

def main():
    corpus_hash = get_hash("experiments/evidence_snapshots/retrieval-v2/documents.json")
    dataset_hash = get_hash("experiments/manifests/retrieval_dataset_v2.json")
    
    with open("experiments/evidence_snapshots/retrieval-v2/manifest.json", "r") as f:
        manifest = json.load(f)
        
    manifest["corpus_sha256"] = corpus_hash
    manifest["dataset_sha256"] = dataset_hash
    manifest["ground_truth_sha256"] = dataset_hash
    
    with open("experiments/evidence_snapshots/retrieval-v2/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Corpus Hash: {corpus_hash}")
    print(f"Dataset Hash: {dataset_hash}")
    
if __name__ == "__main__":
    main()