import hashlib
import io
import logging
from typing import Any, Dict

from PIL import Image

log = logging.getLogger(__name__)

# Constants
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

class ImageValidationError(Exception):
    pass

class ImageValidator:
    """Validates and preprocesses untrusted image uploads."""

    @staticmethod
    def validate_and_preprocess(file_bytes: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """
        Validates an uploaded image and performs minimal preprocessing.
        
        Returns:
            Dict containing validation metadata and original hash.
        """
        # 1. Size Check
        if len(file_bytes) == 0:
            raise ImageValidationError("Uploaded image is empty.")
        if len(file_bytes) > MAX_IMAGE_SIZE_BYTES:
            raise ImageValidationError(f"Image exceeds maximum allowed size of {MAX_IMAGE_SIZE_BYTES // (1024*1024)}MB.")

        # 2. MIME/Extension Check
        if content_type not in ALLOWED_MIME_TYPES:
            raise ImageValidationError(f"Unsupported MIME type: {content_type}")

        ext = filename.lower().split('.')[-1]
        if f".{ext}" not in ALLOWED_EXTENSIONS:
            raise ImageValidationError(f"Unsupported file extension: .{ext}")

        # 3. Compute Hash
        original_hash = hashlib.sha256(file_bytes).hexdigest()

        # 4. Decodability Check (Pillow)
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                img.verify()  # Verify it is a valid image without decoding fully
        except Exception as e:
            log.warning("Image verification failed: %s", e)
            raise ImageValidationError("File is corrupted or not a valid image.")

        # Re-open for actual properties since verify() closes the file
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                width, height = img.size
                img_format = img.format

                # We could do resize/orientation here if needed, but for now we just validate.
                # Returning metadata
                return {
                    "valid": True,
                    "original_image_sha256": original_hash,
                    "format": img_format,
                    "width": width,
                    "height": height,
                    "size_bytes": len(file_bytes),
                    "mime_type": content_type
                }
        except Exception as e:
            log.warning("Image property extraction failed: %s", e)
            raise ImageValidationError("Failed to read image properties.")
