# Prescription Image Pipeline Specification

## Architecture

```
PRESCRIPTION IMAGE
  │
  ▼
FILE VALIDATION (type, size, malicious content)
  │
  ▼
SECURITY SCAN (EXIF stripping, content sanitization)
  │
  ▼
VISION MODEL (Groq Qwen vision — separate from text LLM)
  │
  ▼
STRUCTURED EXTRACTION
  ├── Drug names
  ├── Strengths
  ├── Dosage forms
  ├── Routes
  ├── Frequencies
  └── Instructions
  │
  ▼
CONFIDENCE SCORING (per-field)
  │
  ▼
AMBIGUITY DETECTION
  │
  ▼
USER CONFIRMATION UI
  │
  ▼
CONFIRMED MEDICATIONS → RxNorm → Analysis Pipeline
```

## Vision Model Selection
- Vision/OCR: Groq vision-capable model (e.g., `qwen/qwen3.8-27b`)
- Medical reasoning: Separate text LLM (`openai/gpt-oss-120b`)
- Models are configurable via environment variables
- Never hardcode deprecated model names

## Extraction Output Schema
```json
{
  "extraction_id": "uuid",
  "image_hash": "sha256",
  "model_used": "qwen/qwen3.8-27b",
  "medications": [
    {
      "raw_text": "Tab. Amoxicillin 500mg",
      "drug_name": "Amoxicillin",
      "strength": "500 mg",
      "dosage_form": "Tablet",
      "route": "Oral",
      "frequency": "1-0-1",
      "instructions": "After food",
      "confidence": {
        "drug_name": 0.94,
        "strength": 0.98,
        "frequency": 0.71,
        "overall": 0.88
      }
    }
  ],
  "unreadable_regions": [],
  "overall_confidence": 0.88,
  "requires_confirmation": true
}
```

## Confidence Thresholds
| Level | Threshold | Action |
|-------|-----------|--------|
| HIGH | ≥ 0.85 | Auto-accept, show for review |
| MEDIUM | 0.60–0.84 | Require user confirmation |
| LOW | < 0.60 | Flag as unreadable, require manual entry |

## Failure Modes
| Condition | Response |
|-----------|----------|
| Blurred image | `IMAGE_UNREADABLE` — ask user to retake |
| Handwriting below threshold | `OCR_LOW_CONFIDENCE` — manual entry required |
| Ambiguous drug name | `MEDICATION_AMBIGUOUS` — show candidates for selection |
| Missing critical field | Display with warning, allow user to fill |
| Malicious file detected | `IMAGE_INVALID` — reject silently |

## Privacy
- Prescription images are NOT persisted by default
- Process in memory, discard after extraction
- Never expose uploaded images publicly
- Secure transport (HTTPS) required
- No API credentials in browser
