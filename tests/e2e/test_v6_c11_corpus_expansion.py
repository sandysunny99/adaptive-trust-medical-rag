import pytest
import json
import os

def test_v1_and_v2_corpus_files_exist():
    """Verify that both V1 and V2 corpora exist and V2 is expanded."""
    v1_path = "data/live_medical/LIVE_MEDICAL_CORPUS_V1.json"
    v2_path = "data/live_medical/LIVE_MEDICAL_CORPUS_V2.json"
    
    assert os.path.exists(v1_path)
    assert os.path.exists(v2_path)
    
    with open(v1_path, "r", encoding="utf-8") as f:
        v1 = json.load(f)
        
    with open(v2_path, "r", encoding="utf-8") as f:
        v2 = json.load(f)
        
    assert len(v2) > len(v1)
    
    # Verify categories (anticoagulants, NSAIDs, antibiotics, etc.)
    texts = " ".join([c["text"].lower() for c in v2])
    assert "omeprazole" in texts
    assert "ibuprofen" in texts
    assert "simvastatin" in texts
    assert "metformin" in texts
    assert "lisinopril" in texts
    assert "fluoxetine" in texts
    assert "acetaminophen" in texts

def test_v2_manifest_exists():
    manifest_path = "data/live_medical/LIVE_MEDICAL_CORPUS_MANIFEST_V2.json"
    assert os.path.exists(manifest_path)
    with open(manifest_path, "r", encoding="utf-8") as f:
        m = json.load(f)
        assert m["corpus_version"] == "LIVE_MEDICAL_CORPUS_V2"
        assert m["inherited_from"] == "LIVE_MEDICAL_CORPUS_V1"
        assert m["document_count"] >= 14
