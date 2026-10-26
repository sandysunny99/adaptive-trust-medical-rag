"""Regression tests for defects reproduced by the 2026-10-26 full-system audit
(reports/MEDICAL_RAG_FULL_SYSTEM_AUDIT_2026-10-26.md, defect register AUD-01 to AUD-06; AUD-07 is in
tests/test_trust_gate_rounding.py).

Every image, medication list and evidence text here is synthetic. No provider, model download or
network is contacted: the vision backend, normalizer, retrieval engine and verifier are stubs.
"""

from __future__ import annotations

import asyncio
import io
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from PIL import Image

from adaptive_trust_medical_rag.api.app import app
from adaptive_trust_medical_rag.api.live_schemas import AnalyzeRequest
from adaptive_trust_medical_rag.api.routes import analyze as analyze_route
from adaptive_trust_medical_rag.llm_backend.vision_interfaces import (
    ExtractionConfidence,
    ExtractionResult,
    MedicationCandidate,
)
from adaptive_trust_medical_rag.services import live_application
from adaptive_trust_medical_rag.services.image_validator import ImageValidationError, ImageValidator

client = TestClient(app)


def image_bytes(fmt: str) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color="white").save(buf, format=fmt)
    return buf.getvalue()


def sse_events(text: str) -> list[dict]:
    import json

    events, current = [], {}
    for line in text.splitlines():
        if line.startswith("event: "):
            current["event"] = line[7:]
        elif line.startswith("data: "):
            current["data"] = json.loads(line[6:])
        elif not line and current:
            events.append(current)
            current = {}
    if current:
        events.append(current)
    return events


class RecordingVision:
    provider_name = "stub_vision"
    model_name = "stub-vision-model"

    def __init__(self):
        self.mime_types: list[str] = []

    async def extract_medications(self, image: bytes, mime_type: str) -> ExtractionResult:
        self.mime_types.append(mime_type)
        return ExtractionResult(raw_text="Warfarin 5 mg", candidate_medications=[
            MedicationCandidate(raw_text="Warfarin 5 mg", normalized_text="warfarin",
                                confidence=ExtractionConfidence.HIGH)], warnings=[])


class SlowNormalizer:
    """Holds the pipeline in normalization long enough to post a second confirmation."""

    def __init__(self):
        self.names: list[list[str]] = []

    async def normalize_batch(self, names):
        self.names.append(list(names))
        await asyncio.sleep(0.6)
        return [SimpleNamespace(raw_text=n, generic_name=n.lower(), rxcui=None, brand_name=None,
                                formulation=None, confidence=0.0, source="TEST", metadata={}) for n in names]


@pytest.fixture
def live_state():
    """Stub the components a stream would otherwise load or call, and restore them afterwards."""
    names = ("vision_backend", "drug_normalizer", "retrieval_engine", "claim_verifier")
    saved = {n: getattr(app.state, n, None) for n in names}
    app.state.claim_verifier = object()  # non-None: the lazy loader skips the NLI model
    app.state.retrieval_engine = SimpleNamespace(retrieve=lambda **kw: [])
    yield app.state
    for n, v in saved.items():
        setattr(app.state, n, v)


# ── AUD-01: the vision provider is told the uploaded image's real MIME type ────────────────────

@pytest.mark.parametrize("fmt, filename, declared, expected", [
    ("PNG", "rx.png", "image/png", "image/png"),
    ("WEBP", "rx.webp", "image/webp", "image/webp"),
    ("JPEG", "rx.jpg", "image/jpeg", "image/jpeg"),
])
def test_vision_receives_the_uploaded_image_mime_type(live_state, fmt, filename, declared, expected):
    vision = RecordingVision()
    live_state.vision_backend = vision
    files = {"image": (filename, image_bytes(fmt), declared)}
    req_id = client.post("/api/v1/analyze/prescription", files=files).json()["request_id"]
    client.post(f"/api/v1/analyze/{req_id}/confirm", json={"confirmed_medications": []})
    client.get(f"/api/v1/stream/{req_id}")
    assert vision.mime_types == [expected]


def test_mislabelled_upload_is_sent_with_its_detected_format(live_state):
    """A PNG uploaded as .jpg / image/jpeg is an allowed format, so it is accepted, and the
    provider is told it is a PNG, which is what the bytes are."""
    vision = RecordingVision()
    live_state.vision_backend = vision
    files = {"image": ("rx.jpg", image_bytes("PNG"), "image/jpeg")}
    req_id = client.post("/api/v1/analyze/prescription", files=files).json()["request_id"]
    client.post(f"/api/v1/analyze/{req_id}/confirm", json={"confirmed_medications": []})
    client.get(f"/api/v1/stream/{req_id}")
    assert vision.mime_types == ["image/png"]


# ── AUD-02: the decoded format, not only the declared type and extension, must be allowed ──────

@pytest.mark.parametrize("fmt", ["GIF", "BMP", "TIFF"])
def test_disallowed_image_format_with_allowed_name_and_type_is_rejected(fmt):
    with pytest.raises(ImageValidationError, match="Unsupported image format"):
        ImageValidator.validate_and_preprocess(image_bytes(fmt), "rx.png", "image/png")


def test_allowed_formats_report_their_detected_mime_type():
    for fmt, mime in (("JPEG", "image/jpeg"), ("PNG", "image/png"), ("WEBP", "image/webp")):
        meta = ImageValidator.validate_and_preprocess(image_bytes(fmt), "rx.jpg", "image/jpeg")
        assert meta["detected_mime_type"] == mime
        assert meta["mime_type"] == "image/jpeg"  # the declared type is still recorded


# ── AUD-03: only confirmed medications may be submitted for analysis ───────────────────────────

def _pending_image(request_id: str) -> dict:
    app.state.pending_analyses[request_id] = {"type": "prescription_image"}
    return app.state.pending_analyses[request_id]


@pytest.mark.parametrize("status", ["REJECTED", "UNCERTAIN", "DETECTED", "", "confirmed-ish"])
def test_unconfirmed_statuses_are_refused(status):
    analysis = _pending_image("aud03-" + (status or "empty"))
    try:
        res = client.post(f"/api/v1/analyze/aud03-{status or 'empty'}/confirm", json={
            "confirmed_medications": [{"name": "Warfarin", "status": status, "source": "VISION"}]})
        assert res.status_code == 422
        assert "confirmed_medications" not in analysis
    finally:
        app.state.pending_analyses.pop("aud03-" + (status or "empty"), None)


@pytest.mark.parametrize("name", ["", "   ", "x" * 201])
def test_blank_or_oversized_names_are_refused(name):
    analysis = _pending_image("aud03-name")
    try:
        res = client.post("/api/v1/analyze/aud03-name/confirm", json={
            "confirmed_medications": [{"name": name, "status": "CONFIRMED", "source": "VISION"}]})
        assert res.status_code == 422
        assert "confirmed_medications" not in analysis
    finally:
        app.state.pending_analyses.pop("aud03-name", None)


@pytest.mark.parametrize("status, source", [("CONFIRMED", "VISION"), ("EDITED", "USER_EDITED"),
                                            ("USER_ADDED", "USER")])
def test_statuses_the_confirmation_panel_sends_are_accepted(status, source):
    analysis = _pending_image("aud03-ok")
    try:
        res = client.post("/api/v1/analyze/aud03-ok/confirm", json={
            "confirmed_medications": [{"name": " Warfarin ", "status": status, "source": source}]})
        assert res.status_code == 200
        assert [m.name for m in analysis["confirmed_medications"]] == ["Warfarin"]
    finally:
        app.state.pending_analyses.pop("aud03-ok", None)


# ── AUD-04: a confirmation that arrives after the analysis took one is refused, not ignored ────

async def test_second_confirmation_after_analysis_started_is_refused(live_state):
    live_state.vision_backend = RecordingVision()
    normalizer = SlowNormalizer()
    live_state.drug_normalizer = normalizer
    first = {"confirmed_medications": [{"name": "Warfarin", "status": "CONFIRMED", "source": "VISION"}]}
    second = {"confirmed_medications": [{"name": "Aspirin", "status": "USER_ADDED", "source": "USER"}]}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"image": ("rx.png", image_bytes("PNG"), "image/png")}
        req_id = (await ac.post("/api/v1/analyze/prescription", files=files)).json()["request_id"]
        stream = asyncio.create_task(ac.get(f"/api/v1/stream/{req_id}"))
        await asyncio.sleep(0.3)
        assert (await ac.post(f"/api/v1/analyze/{req_id}/confirm", json=first)).status_code == 200
        await asyncio.sleep(0.2)  # the pipeline has taken the first list and is normalizing it
        late = await ac.post(f"/api/v1/analyze/{req_id}/confirm", json=second)
        events = sse_events((await stream).text)
    assert late.status_code == 409
    assert normalizer.names == [["Warfarin"]]
    rxnorm = next(e for e in events if e["event"] == "rxnorm")
    assert [m["raw_text"] for m in rxnorm["data"]["entities"]] == ["Warfarin"]


# ── AUD-05: a second stream request for the same analysis does not run the pipeline again ──────

async def test_concurrent_stream_requests_run_the_pipeline_once(monkeypatch):
    runs: list[str] = []

    class CountingService:
        def __init__(self, state):
            pass

        async def execute(self, request_id, **kwargs):
            runs.append(request_id)
            yield {"event": "stage_update", "data": {"stage": "uploading", "status": "running"}}
            await asyncio.sleep(0.05)
            yield {"event": "complete", "data": {"request_id": request_id}}

    monkeypatch.setattr(live_application, "LiveMedicalRAGService", CountingService)
    rid = "aud05-req"
    state = SimpleNamespace(pending_analyses={rid: {"body": AnalyzeRequest(drug_names=["warfarin"])}})
    request = SimpleNamespace(app=SimpleNamespace(state=state))

    first = await analyze_route.stream_analysis(rid, request)
    second = await analyze_route.stream_analysis(rid, request)

    async def body(response) -> str:
        return "".join([chunk async for chunk in response.body_iterator])

    first_text, second_text = await asyncio.gather(body(first), body(second))
    assert runs == [rid]
    assert [e["event"] for e in sse_events(first_text)] == ["stage_update", "complete"]
    errors = [e for e in sse_events(second_text) if e["event"] == "error"]
    assert [e["data"]["code"] for e in errors] == ["STREAM_ALREADY_ACTIVE"]
    assert rid not in state.pending_analyses  # the running stream still cleans up


# ── AUD-06: a medication that fails the security checks stops the analysis ─────────────────────

async def test_rejected_medication_name_stops_the_analysis_instead_of_being_dropped():
    normalized: list[list[str]] = []

    class RecordingNormalizer:
        async def normalize_batch(self, names):
            normalized.append(list(names))
            return []

    state = SimpleNamespace(drug_normalizer=RecordingNormalizer(), claim_verifier=object(),
                            retrieval_engine=SimpleNamespace(retrieve=lambda **kw: []))
    service = live_application.LiveMedicalRAGService(state)
    events = [e async for e in service.execute(
        request_id="aud06", drug_names=["warfarin", "<script>alert(1)</script>"],
        patient_context=None, start_time=0.0)]
    assert normalized == []
    assert not any(e["event"] == "rxnorm" for e in events)
    error = next(e for e in events if e["event"] == "error")
    assert error["data"]["code"] == "INPUT_REJECTED"
    assert error["data"]["field"] == "drug_names"
    assert error["data"]["rejected_indices"] == [1]
    # The rejected text is never echoed back.
    assert "script" not in str(error["data"]).lower()
