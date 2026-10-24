"""Vision and OCR provider abstractions for the Medical RAG system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Protocol


class ExtractionConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNCERTAIN = "UNCERTAIN"

@dataclass
class MedicationCandidate:
    raw_text: str
    normalized_text: Optional[str] = None
    confidence: ExtractionConfidence = ExtractionConfidence.UNCERTAIN

@dataclass
class ExtractionResult:
    raw_text: str
    candidate_medications: List[MedicationCandidate]
    warnings: List[str]
    # The model that produced this extraction (the fallback model when it was used).
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    # Every attempt behind this result: model, outcome, failure class, duration. No content.
    attempts: List[dict] = field(default_factory=list)

class VisionProviderAdapter(Protocol):
    """Protocol for providers that extract text/entities from images."""

    async def extract_medications(
        self,
        image_bytes: bytes,
        mime_type: str
    ) -> ExtractionResult:
        """
        Extract medication candidates from an image.
        
        Args:
            image_bytes: The raw image file bytes.
            mime_type: The MIME type of the image (e.g., 'image/jpeg').
            
        Returns:
            ExtractionResult containing the transcribed text and extracted medication candidates.
        """
        ...
