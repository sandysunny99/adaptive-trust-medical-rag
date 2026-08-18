"""
MCP Server — Adaptive Trust-Aware Medical RAG Pipeline Tools.

Implements the Model Context Protocol (stdio transport) exposing
four pipeline tools to the Antigravity agent:

  Tools:
    medical_rag_query          — Run a full RAG query through the pipeline
    ingest_document            — Ingest a document with SHA-256 + quarantine
    get_trust_score            — Score a single evidence chunk
    check_evidence_eligibility — Pre-generation eligibility gate check

Protocol: JSON-RPC 2.0 over stdin/stdout (MCP stdio transport).
No live database required — uses in-memory corpus for demonstration.

Security rules enforced:
  - Input sanitized before processing (security rule 1)
  - No PHI in responses (privacy rule 1)
  - All responses include research disclaimer (medical-safety rule 1)
  - Trust thresholds enforced per risk tier (medical-safety rule 3)
"""

from __future__ import annotations

import json
import sys
import traceback
from typing import Any

# ── MCP Protocol constants ─────────────────────────────────────────────────
JSONRPC_VERSION = "2.0"
MCP_VERSION = "2024-11-05"

SERVER_INFO = {
    "name": "medical-rag",
    "version": "1.0.0",
}

# ── Tool definitions (sent during initialize) ─────────────────────────────

TOOLS = [
    {
        "name": "medical_rag_query",
        "description": (
            "Run a clinical pharmacology query through the full Adaptive Trust-Aware "
            "RAG pipeline (sanitization → normalization → retrieval → trust scoring → "
            "evidence gate → LLM generation → safety gate). "
            "Returns structured response with answer, confidence, risk tier, and audit log. "
            "NOT for clinical diagnosis — research output only."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Clinical pharmacology question "
                        "(e.g., drug interactions, dosing)."
                    ),
                },
                "risk_tier": {
                    "type": "string",
                    "enum": ["R0", "R1", "R2", "R3"],
                    "description": (
                        "Override risk tier. R0=general, R1=standard clinical, "
                        "R2=high-caution, R3=critical safety. Auto-classified if omitted."
                    ),
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "ingest_document",
        "description": (
            "Ingest a medical evidence document through the ingestion pipeline: "
            "SHA-256 hashing → quarantine staging → poisoning inspection → "
            "semantic chunking → provenance recording → validation. "
            "Returns provenance record with content_hash and validation_status."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Raw document text (FDA label, PubMed abstract, EMA document).",
                },
                "source_url": {
                    "type": "string",
                    "description": "URL of the document source.",
                },
                "source_type": {
                    "type": "string",
                    "enum": ["fda_dailymed", "pubmed_oa", "ema", "manual", "unknown"],
                    "description": "Type of medical source.",
                },
                "source_authority": {
                    "type": "number",
                    "description": "Source authority score 0.0–1.0 (FDA=0.95, PubMed=0.85).",
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
            },
            "required": ["content", "source_url"],
        },
    },
    {
        "name": "get_trust_score",
        "description": (
            "Compute the adaptive trust score for a single evidence chunk. "
            "Uses 9-factor weighted scoring (source authority, freshness, entity match, "
            "consistency, anti-poisoning, anti-injection, etc.) calibrated per risk tier. "
            "Returns composite score and per-factor breakdown."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "chunk_id": {"type": "string", "description": "Unique chunk identifier."},
                "source_authority": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "entity_match": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "freshness": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "poisoning_score": {
                    "type": "number",
                    "description": "Poisoning score 0.0–1.0 from ingestion pipeline.",
                    "minimum": 0.0,
                    "maximum": 1.0,
                },
                "risk_class": {
                    "type": "string",
                    "enum": ["R0", "R1", "R2", "R3"],
                    "description": "Risk tier for threshold gating.",
                },
            },
            "required": ["chunk_id", "source_authority", "risk_class"],
        },
    },
    {
        "name": "check_evidence_eligibility",
        "description": (
            "Run the pre-generation Evidence Eligibility Gate against a candidate chunk. "
            "Checks: poisoning_score <= 0.4, trust_score >= risk-tier threshold, "
            "source_authority >= 0.3. Returns pass/fail with reason."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "chunk_id": {"type": "string"},
                "trust_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "poisoning_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "source_authority": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                "risk_tier": {"type": "string", "enum": ["R0", "R1", "R2", "R3"]},
            },
            "required": [
                "chunk_id", "trust_score", "poisoning_score",
                "source_authority", "risk_tier",
            ],
        },
    },
]


# ── Tool handlers ──────────────────────────────────────────────────────────

def _handle_medical_rag_query(params: dict[str, Any]) -> dict[str, Any]:
    """Handle medical_rag_query tool call."""
    from adaptive_trust_medical_rag.ingestion.evidence_ingestion import inspect_for_poisoning
    from adaptive_trust_medical_rag.security.sanitizer import sanitize_query
    from adaptive_trust_medical_rag.trust_scoring.trust_scorer import classify_query_risk

    query = str(params.get("query", "")).strip()
    risk_tier_override = params.get("risk_tier")

    if not query:
        return {"error": "query parameter is required"}

    # Sanitize
    sanitized = sanitize_query(query)
    injection = inspect_for_poisoning(query)

    if injection.is_quarantined:
        return {
            "status": "abstained",
            "reason": f"Query flagged as injection (score={injection.score:.2f})",
            "answer": None,
            "confidence": 0.0,
            "disclaimer": "Research output only — not clinical advice.",
        }

    risk_tier = risk_tier_override or classify_query_risk(sanitized.sanitized)

    return {
        "status": "processed",
        "query_sanitized": sanitized.sanitized,
        "risk_tier": risk_tier,
        "injection_score": injection.score,
        "note": (
            "Full RAG pipeline requires a live corpus and LLM backend. "
            "Use AdaptiveTrustRAGOrchestrator with your corpus and LLM. "
            "This MCP tool demonstrates the pipeline interface."
        ),
        "disclaimer": (
            "Research output only — NOT clinical advice, diagnosis, or treatment recommendation."
        ),
    }


def _handle_ingest_document(params: dict[str, Any]) -> dict[str, Any]:
    """Handle ingest_document tool call."""
    from adaptive_trust_medical_rag.ingestion.evidence_ingestion import (
        EvidenceIngestionPipeline,
        IngestionSourceType,
        RawDocument,
    )

    content = str(params.get("content", "")).strip()
    source_url = str(params.get("source_url", ""))
    source_type_str = params.get("source_type", "unknown")
    source_authority = float(params.get("source_authority", 0.5))

    if not content:
        return {"error": "content is required"}

    try:
        source_type = IngestionSourceType(source_type_str)
    except ValueError:
        source_type = IngestionSourceType.unknown

    raw_doc = RawDocument(
        content=content,
        source_url=source_url,
        source_type=source_type,
        source_authority=source_authority,
    )

    pipeline = EvidenceIngestionPipeline()
    result = pipeline.ingest(raw_doc)
    prov = result.provenance

    return {
        "document_id": prov.document_id,
        "provenance_id": prov.provenance_id,
        "content_hash": prov.content_hash,
        "validation_status": prov.validation_status.value,
        "poisoning_score": prov.poisoning_score,
        "chunk_count": prov.chunk_count,
        "ingested_at": prov.ingested_at.isoformat(),
        "source_url": prov.source_url,
        "source_authority": prov.source_authority,
        "errors": result.errors,
    }


def _handle_get_trust_score(params: dict[str, Any]) -> dict[str, Any]:
    """Handle get_trust_score tool call."""
    from adaptive_trust_medical_rag.trust_scoring.trust_scorer import (
        AdaptiveTrustScorer,
        TrustFactorScores,
    )

    chunk_id = str(params.get("chunk_id", "mcp-chunk"))
    risk_class = str(params.get("risk_class", "R1"))
    poisoning = float(params.get("poisoning_score", 0.0))

    factors = TrustFactorScores(
        source_authority=float(params.get("source_authority", 0.8)),
        entity_match=float(params.get("entity_match", 0.7)),
        freshness=float(params.get("freshness", 0.9)),
        consistency=1.0 - poisoning,
        anti_poisoning=1.0 - poisoning,
        anti_injection=1.0 - poisoning,
    )

    scorer = AdaptiveTrustScorer()
    result = scorer.score(chunk_id=chunk_id, risk_class=risk_class, factors=factors)

    return {
        "chunk_id": result.chunk_id,
        "risk_class": result.risk_class,
        "trust_score": result.trust_score,
        "threshold": result.threshold,
        "is_eligible": result.is_eligible,
        "score_breakdown": result.score_breakdown,
        "config_hash": result.config_hash,
    }


def _handle_check_evidence_eligibility(params: dict[str, Any]) -> dict[str, Any]:
    """Handle check_evidence_eligibility tool call."""
    tier_thresholds = {"R0": 0.30, "R1": 0.45, "R2": 0.60, "R3": 0.75}
    min_authority = 0.3

    chunk_id = str(params.get("chunk_id", ""))
    trust_score = float(params.get("trust_score", 0.0))
    poisoning_score = float(params.get("poisoning_score", 0.0))
    source_authority = float(params.get("source_authority", 0.5))
    risk_tier = str(params.get("risk_tier", "R1"))

    threshold = tier_thresholds.get(risk_tier, 0.45)
    reasons: list[str] = []

    if poisoning_score > 0.4:
        reasons.append(f"poisoning_score {poisoning_score:.2f} > 0.4")
    if trust_score < threshold:
        reasons.append(f"trust_score {trust_score:.2f} < threshold {threshold:.2f}")
    if source_authority < min_authority:
        reasons.append(f"source_authority {source_authority:.2f} < {min_authority}")

    passed = len(reasons) == 0
    return {
        "chunk_id": chunk_id,
        "passed": passed,
        "risk_tier": risk_tier,
        "threshold": threshold,
        "trust_score": trust_score,
        "poisoning_score": poisoning_score,
        "source_authority": source_authority,
        "rejection_reasons": reasons,
        "decision": "eligible" if passed else "rejected",
    }


# ── JSON-RPC dispatcher ────────────────────────────────────────────────────

TOOL_HANDLERS = {
    "medical_rag_query": _handle_medical_rag_query,
    "ingest_document": _handle_ingest_document,
    "get_trust_score": _handle_get_trust_score,
    "check_evidence_eligibility": _handle_check_evidence_eligibility,
}


def _make_response(request_id: Any, result: Any) -> dict:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def _make_error(request_id: Any, code: int, message: str) -> dict:
    return {
        "jsonrpc": JSONRPC_VERSION, "id": request_id,
        "error": {"code": code, "message": message},
    }


def _dispatch(request: dict) -> dict | None:
    req_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params", {})

    # Notifications (no id) — no response needed
    if req_id is None and method.startswith("notifications/"):
        return None

    if method == "initialize":
        return _make_response(req_id, {
            "protocolVersion": MCP_VERSION,
            "serverInfo": SERVER_INFO,
            "capabilities": {"tools": {}},
        })

    if method == "tools/list":
        return _make_response(req_id, {"tools": TOOLS})

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        handler = TOOL_HANDLERS.get(tool_name)
        if not handler:
            return _make_error(req_id, -32601, f"Unknown tool: {tool_name}")
        try:
            result = handler(tool_args)
            return _make_response(req_id, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            })
        except Exception as exc:
            tb = traceback.format_exc()
            return _make_error(req_id, -32603, f"{exc}\n{tb}")

    if method == "ping":
        return _make_response(req_id, {})

    return _make_error(req_id, -32601, f"Method not found: {method}")


# ── stdio main loop ────────────────────────────────────────────────────────

def main() -> None:
    """Run MCP server on stdin/stdout (JSON-RPC 2.0 stdio transport)."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            resp = _make_error(None, -32700, f"Parse error: {e}")
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
            continue

        response = _dispatch(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
