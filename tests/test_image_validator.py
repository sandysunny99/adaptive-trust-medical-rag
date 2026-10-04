import pytest
from io import BytesIO
from PIL import Image
from adaptive_trust_medical_rag.services.image_validator import ImageValidator, ImageValidationError

def create_test_image_bytes(format="JPEG", size=(100, 100)):
    img = Image.new("RGB", size, color="white")
    buf = BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()

def test_valid_image():
    file_bytes = create_test_image_bytes("JPEG")
    res = ImageValidator.validate_and_preprocess(file_bytes, "test.jpg", "image/jpeg")
    assert res["valid"] is True
    assert res["format"] == "JPEG"
    assert "original_image_sha256" in res

def test_empty_image():
    with pytest.raises(ImageValidationError, match="empty"):
        ImageValidator.validate_and_preprocess(b"", "test.jpg", "image/jpeg")

def test_oversized_image():
    file_bytes = b"0" * (6 * 1024 * 1024)
    with pytest.raises(ImageValidationError, match="exceeds maximum"):
        ImageValidator.validate_and_preprocess(file_bytes, "test.jpg", "image/jpeg")

def test_unsupported_mime():
    file_bytes = create_test_image_bytes("JPEG")
    with pytest.raises(ImageValidationError, match="Unsupported MIME"):
        ImageValidator.validate_and_preprocess(file_bytes, "test.jpg", "image/gif")

def test_unsupported_extension():
    file_bytes = create_test_image_bytes("JPEG")
    with pytest.raises(ImageValidationError, match="Unsupported file extension"):
        ImageValidator.validate_and_preprocess(file_bytes, "test.gif", "image/jpeg")

def test_corrupt_image():
    file_bytes = b"this is not an image but it has the right extension"
    with pytest.raises(ImageValidationError, match="corrupted or not a valid image"):
        ImageValidator.validate_and_preprocess(file_bytes, "test.jpg", "image/jpeg")
