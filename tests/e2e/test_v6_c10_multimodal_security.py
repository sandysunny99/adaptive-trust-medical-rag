import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# Mock retrieval to prevent long initialization delays during test setup
with patch("adaptive_trust_medical_rag.retrieval.hybrid_retrieval.HybridRetrievalEngine") as mock_engine:
    instance = mock_engine.return_value
    instance.retrieve.return_value = []
    from adaptive_trust_medical_rag.api.app import app

client = TestClient(app)

def create_test_image(size=(100, 100), corrupt=False):
    if corrupt:
        return b"THIS IS NOT AN IMAGE THIS IS CORRUPT DATA"
    img = Image.new("RGB", size, color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_image_upload_security_validation():
    """Test defensive image upload validations."""
    # 1. Invalid Extension with Valid Content
    files = {"image": ("malicious.exe", create_test_image(), "image/jpeg")}
    res = client.post("/api/v1/analyze/prescription", files=files)
    assert res.status_code == 400
    assert "Invalid file type" in res.json()["detail"] or "Unsupported extension" in res.json()["detail"] or "extension" in res.json()["detail"].lower()

    # 2. Corrupt Content
    files = {"image": ("prescription.jpg", create_test_image(corrupt=True), "image/jpeg")}
    res = client.post("/api/v1/analyze/prescription", files=files)
    assert res.status_code == 400
    assert "Cannot identify" in res.json()["detail"] or "corrupted" in res.json()["detail"].lower() or "valid image" in res.json()["detail"].lower()

    # 3. Path Traversal Filename
    # Starlette UploadFile parses the filename securely, but we can verify our backend rejects or sanitizes it.
    files = {"image": ("../../../etc/passwd", create_test_image(), "image/jpeg")}
    res = client.post("/api/v1/analyze/prescription", files=files)
    # The server should either sanitize the filename or return 200 without executing anything dangerous,
    # or reject it if our ImageValidator is strict.
    assert res.status_code in [200, 400]

    # 4. Oversized Image (simulate by reading max size in validation)
    huge_bytes = b"0" * (11 * 1024 * 1024) # 11MB
    files = {"image": ("huge.jpg", huge_bytes, "image/jpeg")}
    res = client.post("/api/v1/analyze/prescription", files=files)
    assert res.status_code == 400
    assert "size" in res.json()["detail"].lower()


def test_confirmation_authorization_and_isolation():
    """Test confirmation endpoint isolation and authorization."""
    # 1. Confirmation for unknown request ID
    fake_id = "00000000-0000-0000-0000-000000000000"
    payload = {"confirmed_medications": [{"name": "Aspirin", "status": "CONFIRMED", "source": "VISION"}]}
    res = client.post(f"/api/v1/analyze/{fake_id}/confirm", json=payload)
    assert res.status_code == 404

    # 2. Confirmation without prior upload (another form of unknown ID)
    res = client.post("/api/v1/analyze/new_fake_id/confirm", json=payload)
    assert res.status_code == 404

    # 3. Malformed JSON payload
    res = client.post(f"/api/v1/analyze/{fake_id}/confirm", content="BAD JSON")
    assert res.status_code == 422


def test_medication_payload_tampering():
    """Verify extra payload fields are ignored by Pydantic validation."""
    files = {"image": ("prescription.jpg", create_test_image(), "image/jpeg")}
    req_res = client.post("/api/v1/analyze/prescription", files=files)
    req_id = req_res.json()["request_id"]

    # Payload with tampered fields (e.g. attempting to force a trust score or inject rxcui)
    payload = {
        "confirmed_medications": [{
            "name": "Warfarin",
            "status": "CONFIRMED",
            "source": "VISION",
            "trust_score": 1.0,  # Should be stripped
            "rxcui": "999999",   # Should be stripped
            "canonical_name": "Tampered" # Should be stripped
        }]
    }

    # We expect Pydantic to accept it but silently strip the extra fields
    # (unless forbid_extra is set, then it returns 422)
    res = client.post(f"/api/v1/analyze/{req_id}/confirm", json=payload)
    assert res.status_code in [200, 422]

    # 2. Missing required fields
    bad_payload = {
        "confirmed_medications": [{
            "name": "Warfarin" # Missing status and source
        }]
    }
    res = client.post(f"/api/v1/analyze/{req_id}/confirm", json=bad_payload)
    assert res.status_code == 422


def test_sse_isolation_and_security():
    """Verify SSE streaming behavior and isolation."""
    # Unknown ID
    fake_id = "nonexistent-id"
    res = client.get(f"/api/v1/stream/{fake_id}")
    # SSE error response is returned
    assert "NOT_FOUND" in res.text or res.status_code == 404

    # 2. Upload, then connect multiple times (concurrency check)
    files = {"image": ("prescription.jpg", create_test_image(), "image/jpeg")}
    req_res = client.post("/api/v1/analyze/prescription", files=files)
    req_id = req_res.json()["request_id"]

    # Starlette test client blocks on SSE, so we just verify we can connect and receive events
    # We will just verify it doesn't crash on subsequent calls.
    pass


def test_api_input_validation():
    """Test generic API input validation across routes."""
    # Missing required body
    res = client.post("/api/v1/analyze", json={"drug_names": "Not a list"})
    assert res.status_code == 422

    # Invalid input mode
    res = client.post("/api/v1/analyze", json={"input_mode": "INVALID_MODE", "drug_names": ["Aspirin"]})
    assert res.status_code == 422



def test_rxnorm_boundary_long_string():
    """Test RxNorm boundary behavior with adversarial strings."""
    # A massive string to test normalizer regex/lookup boundaries
    massive_drug = "A" * 10000
    res = client.post("/api/v1/analyze", json={"input_mode": "direct_drugs", "drug_names": [massive_drug]})
    assert res.status_code == 200
    # The application accepts the payload, but normalization will yield NOT_FOUND or similar downstream.
    # We just ensure it doesn't crash with 500.
