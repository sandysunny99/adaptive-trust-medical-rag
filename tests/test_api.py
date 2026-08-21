"""
Tests for Phase 19 - FastAPI HTTP Layer.

Uses httpx AsyncClient with the TestClient pattern (no live DB/LLM).
A MockPipeline is injected via app.state for /query tests.
Covers: query, ingest, health, audit endpoints + middleware.
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from adaptive_trust_medical_rag.api.app import create_app
from adaptive_trust_medical_rag.orchestrator.rag_orchestrator import (
    PipelineStatus,
    RAGRequest,
    RAGResponse,
)
from adaptive_trust_medical_rag.verification.claim_verifier import (
    GateDecision,
    VerificationReport,
)

# ── Test doubles ──────────────────────────────────────────────────────────────

def _make_rag_response(
    status: PipelineStatus = PipelineStatus.released,
    confidence: float = 0.85,
    answer: str = "Warfarin inhibits VKORC1 [Source 1].",
) -> RAGResponse:
    vr = VerificationReport(
        claims=[],
        alignments=[],
        contradictions=[],
        grounding_ratio=0.90,
        mean_citation_trust=0.88,
        contradiction_score=0.0,
        confidence=confidence,
        decision=GateDecision.release
        if status == PipelineStatus.released
        else GateDecision.abstain,
        explanation="Mock verification",
    )
    return RAGResponse(
        session_id="test-session-001",
        query_hash="abc123def456",
        risk_tier="R1",
        status=status,
        answer=answer,
        confidence=confidence,
        trust_scores=[0.88, 0.75],
        retrieved_chunk_ids=["chunk-1", "chunk-2"],
        gate_decision=vr.decision.value,
        verification_report=vr,
        audit_log={},
    )


class MockPipeline:
    def __init__(self, response: RAGResponse | None = None) -> None:
        self._response = response or _make_rag_response()
        self.calls: list[RAGRequest] = []

    def __call__(self, req: RAGRequest) -> RAGResponse:
        self.calls.append(req)
        return self._response


class ErrorPipeline:
    def __call__(self, req: RAGRequest) -> RAGResponse:
        raise RuntimeError("Pipeline exploded!")


def _make_client(
    pipeline: Any = None,
    rate_limit: int = 1000,
) -> TestClient:
    app = create_app(pipeline=pipeline, rate_limit=rate_limit, rate_window=60)
    return TestClient(app, raise_server_exceptions=False)


# ── POST /query ───────────────────────────────────────────────────────────────

class TestQueryEndpoint:
    def test_valid_query_returns_200(self) -> None:
        client = _make_client(MockPipeline())
        resp = client.post("/query", json={"query": "What is the mechanism of warfarin?"})
        assert resp.status_code == 200

    def test_response_has_required_fields(self) -> None:
        client = _make_client(MockPipeline())
        resp = client.post("/query", json={"query": "What is the mechanism of warfarin?"})
        data = resp.json()
        for field in ["session_id", "query_hash", "risk_tier", "status", "answer",
                      "confidence", "gate_decision", "disclaimer"]:
            assert field in data, f"Missing field: {field}"

    def test_disclaimer_always_present(self) -> None:
        client = _make_client(MockPipeline())
        resp = client.post("/query", json={"query": "What is metformin used for?"})
        assert "RESEARCH OUTPUT ONLY" in resp.json()["disclaimer"]

    def test_citations_returned(self) -> None:
        client = _make_client(MockPipeline())
        resp = client.post("/query", json={"query": "What is the mechanism of warfarin?"})
        data = resp.json()
        assert len(data["citations"]) == 2
        assert data["citations"][0]["chunk_id"] == "chunk-1"

    def test_abstained_response_has_reason(self) -> None:
        abstained = _make_rag_response(
            status=PipelineStatus.abstained, confidence=0.0,
            answer="[SYSTEM ABSTENTION: insufficient evidence]"
        )
        client = _make_client(MockPipeline(abstained))
        resp = client.post("/query", json={"query": "What is the mechanism of warfarin?"})
        data = resp.json()
        assert data["status"] == "abstained"
        assert data["abstention_reason"] is not None

    def test_no_pipeline_returns_503(self) -> None:
        client = _make_client(pipeline=None)
        resp = client.post("/query", json={"query": "What is warfarin?"})
        assert resp.status_code == 503

    def test_pipeline_error_returns_500(self) -> None:
        client = _make_client(ErrorPipeline())
        resp = client.post("/query", json={"query": "What is warfarin?"})
        assert resp.status_code == 500

    def test_query_too_short_returns_422(self) -> None:
        client = _make_client(MockPipeline())
        resp = client.post("/query", json={"query": "Hi"})
        assert resp.status_code == 422

    def test_query_too_long_returns_422(self) -> None:
        client = _make_client(MockPipeline())
        resp = client.post("/query", json={"query": "x" * 3000})
        assert resp.status_code == 422

    def test_phi_ssn_rejected_422(self) -> None:
        client = _make_client(MockPipeline())
        body = {"query": "Patient SSN 123-45-6789 needs warfarin"}
        resp = client.post("/query", json=body)
        assert resp.status_code == 422

    def test_session_id_forwarded(self) -> None:
        mp = MockPipeline()
        client = _make_client(mp)
        resp = client.post("/query", json={
            "query": "What is the mechanism of warfarin?",
            "session_id": "my-session-abc"
        })
        assert resp.status_code == 200
        assert len(mp.calls) == 1
        assert mp.calls[0].session_id == "my-session-abc"

    def test_risk_tier_override_forwarded(self) -> None:
        mp = MockPipeline()
        client = _make_client(mp)
        resp = client.post("/query", json={
            "query": "What is the mechanism of warfarin?",
            "risk_tier_override": "R3"
        })
        assert resp.status_code == 200
        assert mp.calls[0].risk_tier_override == "R3"

    def test_invalid_risk_tier_override_422(self) -> None:
        client = _make_client(MockPipeline())
        resp = client.post("/query", json={
            "query": "What is warfarin?",
            "risk_tier_override": "R9"
        })
        assert resp.status_code == 422

    def test_request_id_header_returned(self) -> None:
        client = _make_client(MockPipeline())
        resp = client.post("/query", json={"query": "What is the mechanism of warfarin?"})
        assert "x-request-id" in resp.headers

    def test_security_headers_present(self) -> None:
        client = _make_client(MockPipeline())
        resp = client.post("/query", json={"query": "What is the mechanism of warfarin?"})
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("cache-control") == "no-store"


# ── POST /ingest ──────────────────────────────────────────────────────────────

class TestIngestEndpoint:
    def _ingest_body(self) -> dict:
        return {
            "title": "Warfarin Drug Interactions Review",
            "content": "Warfarin interacts with rifampin via CYP2C9 induction. " * 20,
            "source_tier": "tier_3_primary",
            "publication_year": 2023,
        }

    def test_valid_ingest_returns_200(self) -> None:
        client = _make_client()
        resp = client.post("/ingest", json=self._ingest_body())
        assert resp.status_code == 200

    def test_response_has_document_id(self) -> None:
        client = _make_client()
        resp = client.post("/ingest", json=self._ingest_body())
        data = resp.json()
        assert "document_id" in data
        assert len(data["document_id"]) > 0

    def test_response_has_content_hash(self) -> None:
        client = _make_client()
        resp = client.post("/ingest", json=self._ingest_body())
        data = resp.json()
        assert "content_hash" in data
        assert len(data["content_hash"]) == 64  # SHA-256 hex

    def test_same_content_same_hash(self) -> None:
        client = _make_client()
        body = self._ingest_body()
        r1 = client.post("/ingest", json=body).json()
        r2 = client.post("/ingest", json=body).json()
        assert r1["content_hash"] == r2["content_hash"]

    def test_missing_title_returns_422(self) -> None:
        client = _make_client()
        body = self._ingest_body()
        del body["title"]
        resp = client.post("/ingest", json=body)
        assert resp.status_code == 422

    def test_content_too_short_returns_422(self) -> None:
        client = _make_client()
        body = self._ingest_body()
        body["content"] = "short"
        resp = client.post("/ingest", json=body)
        assert resp.status_code == 422

    def test_invalid_source_tier_returns_422(self) -> None:
        client = _make_client()
        body = self._ingest_body()
        body["source_tier"] = "tier_99_fake"
        resp = client.post("/ingest", json=body)
        assert resp.status_code == 422

    def test_request_id_header_on_ingest(self) -> None:
        client = _make_client()
        resp = client.post("/ingest", json=self._ingest_body())
        assert "x-request-id" in resp.headers


# ── GET /health ───────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_200(self) -> None:
        client = _make_client()
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_has_status_field(self) -> None:
        client = _make_client()
        resp = client.get("/health")
        assert "status" in resp.json()

    def test_health_status_unhealthy_without_db(self) -> None:
        client = _make_client()
        data = client.get("/health").json()
        # No DB configured in test mode
        assert data["status"] == "unhealthy"
        assert data["database"] is False

    def test_health_version_present(self) -> None:
        client = _make_client()
        data = client.get("/health").json()
        assert data["version"] == "1.0.0"

    def test_health_uptime_present(self) -> None:
        client = _make_client()
        data = client.get("/health").json()
        assert data["uptime_seconds"] is not None
        assert data["uptime_seconds"] >= 0

    def test_health_with_mock_db_checker_ok(self) -> None:
        async def checker():
            return {"db": True, "pgvector": True}
        app = create_app(db_health_checker=checker)
        client = TestClient(app)
        data = client.get("/health").json()
        assert data["status"] == "ok"
        assert data["database"] is True
        assert data["pgvector"] is True

    def test_health_with_degraded_db(self) -> None:
        async def checker():
            return {"db": True, "pgvector": False}
        app = create_app(db_health_checker=checker)
        client = TestClient(app)
        data = client.get("/health").json()
        assert data["status"] == "degraded"


# ── GET /audit ────────────────────────────────────────────────────────────────

class TestAuditEndpoint:
    def test_audit_returns_200_no_store(self) -> None:
        client = _make_client()
        resp = client.get("/audit/test-session-001")
        assert resp.status_code == 200

    def test_audit_empty_events_without_store(self) -> None:
        client = _make_client()
        data = client.get("/audit/test-session-001").json()
        assert data["event_count"] == 0
        assert data["events"] == []

    def test_audit_session_id_in_response(self) -> None:
        client = _make_client()
        data = client.get("/audit/my-session-xyz").json()
        assert data["session_id"] == "my-session-xyz"

    def test_audit_too_short_session_id_400(self) -> None:
        client = _make_client()
        resp = client.get("/audit/ab")
        assert resp.status_code == 400

    def test_audit_too_long_session_id_400(self) -> None:
        client = _make_client()
        resp = client.get("/audit/" + "x" * 65)
        assert resp.status_code == 400

    def test_audit_with_mock_store(self) -> None:
        class MockAuditStore:
            async def get_events(self, session_id: str) -> list[dict]:
                return [{
                    "event_id": "evt-001",
                    "session_id": session_id,
                    "query_hash": "abc123",
                    "risk_class": "R1",
                    "gate_decision": "release",
                    "trust_score": 0.85,
                    "confidence": 0.90,
                    "created_at": "2026-08-21T10:00:00Z",
                }]
        app = create_app(audit_store=MockAuditStore())
        client = TestClient(app)
        data = client.get("/audit/test-session").json()
        assert data["event_count"] == 1
        assert data["events"][0]["query_hash"] == "abc123"


# ── Rate limiting ─────────────────────────────────────────────────────────────

class TestRateLimiting:
    def test_rate_limit_triggers_429(self) -> None:
        # limit=2: third request must be 429
        client = _make_client(MockPipeline(), rate_limit=2)
        client.post("/query", json={"query": "What is warfarin?"})
        client.post("/query", json={"query": "What is warfarin?"})
        resp = client.post("/query", json={"query": "What is warfarin?"})
        assert resp.status_code == 429

    def test_rate_limit_response_has_retry_after(self) -> None:
        client = _make_client(MockPipeline(), rate_limit=1)
        client.post("/query", json={"query": "What is warfarin?"})
        resp = client.post("/query", json={"query": "What is warfarin?"})
        if resp.status_code == 429:
            assert "retry-after" in resp.headers

    def test_health_exempt_from_rate_limit(self) -> None:
        client = _make_client(rate_limit=1)
        for _ in range(10):
            resp = client.get("/health")
            assert resp.status_code == 200
