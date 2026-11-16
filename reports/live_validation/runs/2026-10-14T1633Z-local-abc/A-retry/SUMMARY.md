# A/B/C run summary

Every value below is read from the saved events of this run.

| Scenario | Embedding | Retrieved | Eligible | Unrelated excluded | Risk | Threshold | Terminal |
|---|---|---|---|---|---|---|---|
| A-image | None (None) | None | None | None | None | None | None  |

## A-image

- Requests: POST /api/v1/analyze/prescription -> 200, POST /api/v1/analyze/b85ccd62-7cd6-4ff5-b6a1-7c4be48e0400/confirm -> 200
- Patient context sent: `null`
- Risk basis: None
- Terminal reason: None
- Removed disclaimers: None
- Confirmation (200): `{"confirmed_medications": [{"name": "Simvastatin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Simvastatin"}, {"name": "Clarithromycin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Clarithromycin"}]}`

## Credential-shaped strings

None found.
