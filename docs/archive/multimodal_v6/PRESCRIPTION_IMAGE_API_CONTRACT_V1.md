# Prescription Image API Contract V1

## POST /api/v1/analyze/prescription
**Content-Type**: `multipart/form-data`
Accepts an image upload alongside optional patient context.

**Request Payload:**
- `image`: File (png, jpeg, webp)
- `patient_context`: JSON string (optional)

**Response:**
Returns `{ "request_id": "uuid", "stream_url": "/api/v1/stream/{request_id}" }`

## GET /api/v1/stream/{request_id}
Extended SSE lifecycle for image processing.
Events:
1. `image_received`
2. `image_validated`
3. `vision_started`
4. `medication_candidates_extracted`
   *Payload contains candidates requiring user confirmation. Stream remains open.*
5. `medications_confirmed` (emitted once user submits confirmation)
6. Standard RAG lifecycle (`retrieving`, `trust_evaluating`, etc.)
7. `answer` / `abstention`
8. `complete`

## POST /api/v1/analyze/{request_id}/confirm
**Content-Type**: `application/json`
User submits the confirmed drug names.

**Request Payload:**
```json
{
  "confirmed_medications": ["warfarin", "aspirin"]
}
```

**Response:**
Returns `{ "status": "accepted" }`
Triggers the backend pipeline to resume processing the request on the SSE stream.
