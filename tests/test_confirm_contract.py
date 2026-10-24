"""Contract of POST /api/v1/analyze/{request_id}/confirm (ConfirmMedicationsRequest).

The frontend once sent bare names; the model takes objects and must keep
rejecting strings with a 422 rather than guessing their status and source.
"""

import asyncio

import pytest
from fastapi.testclient import TestClient

from adaptive_trust_medical_rag.api.app import app

client = TestClient(app)
ITEMS = [
    {"name": "Simvastatin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Simvastatin 40 mg"},
    {"name": "Clarithromycin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Clarithromycin 500 mg"},
]


def _pending(request_id, **state):
    """A request whose extraction finished and which now waits for the user's confirmation."""
    app.state.pending_analyses = getattr(app.state, "pending_analyses", {}) or {}
    app.state.pending_analyses[request_id] = {"type": "prescription_image", "awaiting_confirmation": True,
                                              "confirmation_event": asyncio.Event(), **state}
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


def test_an_identical_repeat_is_acknowledged_and_changes_nothing():
    analysis = _pending("req-twice")
    try:
        first = client.post("/api/v1/analyze/req-twice/confirm", json={"confirmed_medications": ITEMS})
        stored = analysis["confirmed_medications"]
        second = client.post("/api/v1/analyze/req-twice/confirm", json={"confirmed_medications": ITEMS})
        assert (first.status_code, first.json()["status"]) == (200, "success")
        assert (second.status_code, second.json()["status"]) == (200, "already_confirmed")
        assert analysis["confirmed_medications"] is stored
    finally:
        app.state.pending_analyses.pop("req-twice", None)


def test_a_different_second_confirmation_is_refused_and_the_first_stands():
    analysis = _pending("req-conflict")
    try:
        assert client.post("/api/v1/analyze/req-conflict/confirm", json={"confirmed_medications": ITEMS}).status_code == 200
        second = client.post("/api/v1/analyze/req-conflict/confirm", json={"confirmed_medications": ITEMS[:1]})
        assert second.status_code == 409 and "already accepted" in second.json()["detail"]
        assert [m.model_dump() for m in analysis["confirmed_medications"]] == ITEMS
    finally:
        app.state.pending_analyses.pop("req-conflict", None)


def test_a_confirmation_before_extraction_finishes_is_refused_and_stores_nothing():
    analysis = _pending("req-early", awaiting_confirmation=False)
    try:
        response = client.post("/api/v1/analyze/req-early/confirm", json={"confirmed_medications": ITEMS})
        assert response.status_code == 409 and "not waiting" in response.json()["detail"]
        assert "confirmed_medications" not in analysis and not analysis["confirmation_event"].is_set()
    finally:
        app.state.pending_analyses.pop("req-early", None)


def test_a_confirmation_after_the_analysis_ended_is_refused():
    # Extraction failed or the confirmation timed out: the request is finished but not yet removed.
    analysis = _pending("req-ended", finished=True)
    try:
        response = client.post("/api/v1/analyze/req-ended/confirm", json={"confirmed_medications": ITEMS})
        assert response.status_code == 409 and "already ended" in response.json()["detail"]
        assert "confirmed_medications" not in analysis and not analysis["confirmation_event"].is_set()
    finally:
        app.state.pending_analyses.pop("req-ended", None)


@pytest.mark.parametrize("items", [
    [], [{**ITEMS[0], "name": "   "}], [{**ITEMS[0], "status": "UNCERTAIN"}], [{**ITEMS[0], "status": "DETECTED"}]])
def test_an_empty_or_unreviewed_selection_is_rejected(items):
    analysis = _pending("req-bad")
    try:
        response = client.post("/api/v1/analyze/req-bad/confirm", json={"confirmed_medications": items})
        assert response.status_code == 422
        assert "confirmed_medications" not in analysis and not analysis["confirmation_event"].is_set()
    finally:
        app.state.pending_analyses.pop("req-bad", None)


def test_an_old_requests_confirmation_cannot_touch_a_newer_request():
    newer = _pending("req-new")
    try:
        old = client.post("/api/v1/analyze/req-old-finished/confirm", json={"confirmed_medications": ITEMS})
        assert old.status_code == 404
        assert "confirmed_medications" not in newer and not newer["confirmation_event"].is_set()
    finally:
        app.state.pending_analyses.pop("req-new", None)


def test_unknown_request_is_404():
    response = client.post("/api/v1/analyze/req-missing/confirm", json={"confirmed_medications": ITEMS})
    assert response.status_code == 404
