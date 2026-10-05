import io

from fastapi.testclient import TestClient
from PIL import Image

from adaptive_trust_medical_rag.api.app import app

client = TestClient(app)

def create_test_image_bytes(format="JPEG", size=(100, 100)):
    img = Image.new("RGB", size, color="white")
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()

def test_post_analyze_prescription_valid():
    file_bytes = create_test_image_bytes("JPEG")
    files = {"image": ("test.jpg", file_bytes, "image/jpeg")}

    response = client.post("/api/v1/analyze/prescription", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "stream_url" in data
    assert data["validation"]["valid"] is True
    assert data["validation"]["mime_type"] == "image/jpeg"

def test_post_analyze_prescription_oversized():
    file_bytes = b"0" * (6 * 1024 * 1024)
    files = {"image": ("big.jpg", file_bytes, "image/jpeg")}
    response = client.post("/api/v1/analyze/prescription", files=files)
    assert response.status_code == 400
    assert "exceeds maximum" in response.json()["detail"]

def test_post_analyze_prescription_invalid_type():
    file_bytes = create_test_image_bytes("JPEG")
    files = {"image": ("test.gif", file_bytes, "image/gif")}
    response = client.post("/api/v1/analyze/prescription", files=files)
    assert response.status_code == 400
    assert "Unsupported MIME" in response.json()["detail"]

def test_post_analyze_prescription_corrupt():
    file_bytes = b"not an image"
    files = {"image": ("test.jpg", file_bytes, "image/jpeg")}
    response = client.post("/api/v1/analyze/prescription", files=files)
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"]

def test_post_analyze_prescription_with_context():
    file_bytes = create_test_image_bytes("PNG")
    files = {"image": ("test.png", file_bytes, "image/png")}
    data = {"patient_context": '{"age": 45}'}
    response = client.post("/api/v1/analyze/prescription", files=files, data=data)
    assert response.status_code == 200
    assert "request_id" in response.json()

def test_post_analyze_prescription_bad_context():
    file_bytes = create_test_image_bytes("PNG")
    files = {"image": ("test.png", file_bytes, "image/png")}
    data = {"patient_context": '{bad json}'}
    response = client.post("/api/v1/analyze/prescription", files=files, data=data)
    assert response.status_code == 400
    assert "Invalid patient_context" in response.json()["detail"]
