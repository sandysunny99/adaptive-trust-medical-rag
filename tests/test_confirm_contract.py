"""Contract of POST /api/v1/analyze/{request_id}/confirm (ConfirmMedicationsRequest).

The frontend once sent bare names; the model takes objects and must keep
rejecting strings with a 422 rather than guessing their status and source.
"""

from fastapi.testclient import TestClient

from adaptive_trust_medical_rag.api.app import app

client = TestClient(app)
ITEMS = [
    {"name": "Simvastatin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Simvastatin 40 mg"},
    {"name": "Clarithromycin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Clarithromycin 500 mg"},
]


def _pending(request_id):
    app.state.pending_analyses = getattr(app.state, "pending_analyses", {}) or {}
    app.state.pending_analyses[request_id] = {"type": "prescription_image"}
    return app.state.pending_analyses[request_id]


def test_objects_are_accepted_and_stored_in_order():
    analysis = _pending("req-objects")
    try:
        response = client.post("/api/v1/analyze/req-objects/confirm", json={"confirmed_medications": ITEMS})
        assert response.status_code == 200
        stored = [m.model_dump() for m in analysis["confirmed_medications"]]
        assert stored == ITEMS
    finally:
        app.state.pending_analyses.pop("req-objects", None)


def test_bare_names_are_rejected_per_item():
    analysis = _pending("req-strings")
    try:
        response = client.post("/api/v1/analyze/req-strings/confirm",
                               json={"confirmed_medications": ["Simvastatin", "Clarithromycin"]})
        assert response.status_code == 422
        locs = [e["loc"] for e in response.json()["detail"]]
        assert locs == [["body", "confirmed_medications", 0], ["body", "confirmed_medications", 1]]
        assert "confirmed_medications" not in analysis
    finally:
        app.state.pending_analyses.pop("req-strings", None)


def test_unknown_request_is_404():
    response = client.post("/api/v1/analyze/req-missing/confirm", json={"confirmed_medications": ITEMS})
    assert response.status_code == 404
