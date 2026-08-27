"""Tests for F0/F1 Integrity Auditor

Project: Adaptive Trust-Aware Medical RAG
File: tests/test_f0_f1_integrity.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adaptive_trust_medical_rag.evaluation.f0_f1_integrity import (
    F0F1IntegrityAuditor,
)


@pytest.fixture
def temp_run_dir(tmp_path: Path) -> Path:
    """Fixture providing a temporary run directory."""
    run_dir = tmp_path / "f0-f1-test"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _make_case_row(
    case_id: str,
    variant: str,
    evidence_backend: str,
    faithfulness: float,
    hallucination: float,
    p0_count: int = 0,
) -> dict:
    return {
        "experiment_id": "test-exp",
        "case_id": case_id,
        "variant": variant,
        "pipeline_mode": "DETERMINISTIC_MOCK",
        "evidence_backend": evidence_backend,
        "query_hash": f"hash_{case_id}",
        "risk_tier": "R1",
        "retrieved_document_ids": ["doc-1", "doc-2"],
        "p0_document_ids": [f"p0-{i}" for i in range(p0_count)],
        "p0_retrieved_count": p0_count,
        "trust_scores": [0.85, 0.90],
        "generated_answer_hash": f"ans_hash_{case_id}_{variant}",
        "claims": ["Claim 1", "Claim 2"],
        "claim_verification": ["SUPPORTED", "SUPPORTED"],
        "citations": ["doc-1"],
        "faithfulness": faithfulness,
        "hallucination_rate": hallucination,
        "citation_precision": 1.0,
        "abstained": False,
        "latency_ms": 12.5,
    }


def test_audit_valid_run(temp_run_dir: Path) -> None:
    """Test auditor passes on valid paired empirical case execution."""
    jsonl_file = temp_run_dir / "case_results.jsonl"
    rows = []

    # 5 paired cases with varied empirical differences
    faith_f0 = [0.80, 0.85, 0.75, 0.90, 0.70]
    faith_f1 = [0.85, 0.88, 0.80, 0.90, 0.76]  # Non-identical deltas: 0.05, 0.03, 0.05, 0.0, 0.06

    for i in range(5):
        cid = f"case_{i:03d}"
        rows.append(_make_case_row(cid, "F0", "BASE_CORPUS", faith_f0[i], 0.10, 0))
        rows.append(_make_case_row(cid, "F1", "BASE_CORPUS_PLUS_P0", faith_f1[i], 0.05, 1))

    with jsonl_file.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    summary_file = temp_run_dir / "summary.json"
    summary_data = {
        "f0": {"faithfulness": sum(faith_f0) / len(faith_f0)},
        "f1": {"faithfulness": sum(faith_f1) / len(faith_f1)},
    }
    summary_file.write_text(json.dumps(summary_data), encoding="utf-8")

    auditor = F0F1IntegrityAuditor()
    report = auditor.audit_run_directory(temp_run_dir)

    assert report.verdict == "PASS"
    assert report.paired_cases == 5
    assert report.is_valid_research_experiment()
    assert report.p0_utilization_verified
    assert report.evidence_difference_verified
    assert not report.hard_coded_delta_detected


def test_audit_missing_case_results(temp_run_dir: Path) -> None:
    """Test auditor fails when case_results.jsonl is missing."""
    auditor = F0F1IntegrityAuditor()
    report = auditor.audit_run_directory(temp_run_dir)
    assert report.verdict == "FAIL"
    assert "case_results.jsonl missing" in report.findings[0]


def test_audit_hard_coded_delta_detection(temp_run_dir: Path) -> None:
    """Test auditor detects synthetic constant delta patterns across all cases."""
    jsonl_file = temp_run_dir / "case_results.jsonl"
    rows = []

    # Exactly 0.0300 delta on every single case
    for i in range(10):
        cid = f"case_{i:03d}"
        rows.append(_make_case_row(cid, "F0", "BASE_CORPUS", 0.85, 0.05, 0))
        rows.append(_make_case_row(cid, "F1", "BASE_CORPUS_PLUS_P0", 0.88, 0.02, 1))

    with jsonl_file.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    auditor = F0F1IntegrityAuditor()
    report = auditor.audit_run_directory(temp_run_dir)

    assert report.verdict == "FAIL"
    assert report.hard_coded_delta_detected
    assert any("Suspicious constant delta" in f for f in report.findings)


def test_audit_unpaired_cases(temp_run_dir: Path) -> None:
    """Test auditor warns on unpaired case IDs."""
    jsonl_file = temp_run_dir / "case_results.jsonl"
    rows = [
        _make_case_row("case_001", "F0", "BASE_CORPUS", 0.80, 0.10, 0),
        _make_case_row("case_001", "F1", "BASE_CORPUS_PLUS_P0", 0.85, 0.05, 1),
        _make_case_row("case_002", "F0", "BASE_CORPUS", 0.75, 0.15, 0),  # Missing in F1
    ]

    with jsonl_file.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    auditor = F0F1IntegrityAuditor()
    report = auditor.audit_run_directory(temp_run_dir)
    assert report.verdict == "WARN"
    assert any("Cases missing in F1" in f for f in report.findings)


def test_audit_mismatched_summary(temp_run_dir: Path) -> None:
    """Test auditor fails if summary.json metrics diverge from JSONL averages."""
    jsonl_file = temp_run_dir / "case_results.jsonl"
    rows = [
        _make_case_row("case_001", "F0", "BASE_CORPUS", 0.80, 0.10, 0),
        _make_case_row("case_001", "F1", "BASE_CORPUS_PLUS_P0", 0.85, 0.05, 1),
    ]

    with jsonl_file.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    summary_file = temp_run_dir / "summary.json"
    # Report 0.99 when actual is 0.80
    summary_file.write_text(json.dumps({"f0": {"faithfulness": 0.99}}), encoding="utf-8")

    auditor = F0F1IntegrityAuditor()
    report = auditor.audit_run_directory(temp_run_dir)
    assert report.verdict == "FAIL"
    assert any("Summary F0 faithfulness" in f for f in report.findings)
