"""Vision and OCR provider abstractions for the Medical RAG system."""

from typing import Protocol, List, Optional
from dataclasses import dataclass
from enum import Enum

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
