import os
import json
import csv
from pathlib import Path
import pytest
from adaptive_trust_medical_rag.security_evaluation.review_auditor import HumanReviewAuditor

def test_auditor_missing_files(tmp_path):
    auditor = HumanReviewAuditor(str(tmp_path / "missing.jsonl"), str(tmp_path / "missing.csv"))
    result = auditor.audit()
    assert result.is_complete is False
    assert result.is_freeze_eligible is False
    assert any("missing" in e.lower() for e in result.errors)

def test_auditor_blank_worksheet(tmp_path):
    # Setup candidate
    cand_path = tmp_path / "cand.jsonl"
    with open(cand_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"case_id": "SEC_1", "payload": "test", "requires_authorization_check": False, "requires_provenance_preservation": False}) + "\n")
        f.write(json.dumps({"case_id": "SEC_2", "payload": "test2", "requires_authorization_check": True, "requires_provenance_preservation": False}) + "\n")

    # Setup blank csv
    csv_path = tmp_path / "rev.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "payload", "requires_authorization_check", "requires_provenance_preservation", "reviewer_decision"])
        writer.writeheader()
        writer.writerow({"case_id": "SEC_1", "payload": "test", "requires_authorization_check": "False", "requires_provenance_preservation": "False", "reviewer_decision": ""})
        writer.writerow({"case_id": "SEC_2", "payload": "test2", "requires_authorization_check": "True", "requires_provenance_preservation": "False", "reviewer_decision": ""})

    auditor = HumanReviewAuditor(str(cand_path), str(csv_path))
    result = auditor.audit()
    assert result.is_complete is False
    assert result.total_cases == 2
    assert result.reviewed_cases == 0
    assert any("Missing reviewer_decision" in e for e in result.errors)

def test_auditor_payload_mismatch(tmp_path):
    # Setup candidate
    cand_path = tmp_path / "cand.jsonl"
    with open(cand_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"case_id": "SEC_1", "payload": "test", "requires_authorization_check": False, "requires_provenance_preservation": False}) + "\n")

    # Setup mismatched csv
    csv_path = tmp_path / "rev.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "payload", "requires_authorization_check", "requires_provenance_preservation", "reviewer_decision", "reviewer_id", "review_timestamp", "review_semantic_distinctness"])
        writer.writeheader()
        writer.writerow({
            "case_id": "SEC_1", 
            "payload": "CHANGED_PAYLOAD", 
            "requires_authorization_check": "False", 
            "requires_provenance_preservation": "False", 
            "reviewer_decision": "ACCEPT",
            "reviewer_id": "R1",
            "review_timestamp": "2026",
            "review_semantic_distinctness": "PASS"
        })

    auditor = HumanReviewAuditor(str(cand_path), str(csv_path))
    result = auditor.audit()
    assert result.is_complete is False
    assert any("Payload mismatch" in e for e in result.errors)

def test_auditor_perfect_freeze_eligible(tmp_path):
    cand_path = tmp_path / "cand.jsonl"
    with open(cand_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"case_id": "SEC_1", "payload": "test", "requires_authorization_check": False, "requires_provenance_preservation": False}) + "\n")

    csv_path = tmp_path / "rev.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "payload", "requires_authorization_check", "requires_provenance_preservation", "reviewer_decision", "reviewer_id", "review_timestamp", "review_semantic_distinctness", "review_implementation_leakage"])
        writer.writeheader()
        writer.writerow({
            "case_id": "SEC_1", 
            "payload": "test", 
            "requires_authorization_check": "False", 
            "requires_provenance_preservation": "False", 
            "reviewer_decision": "ACCEPT",
            "reviewer_id": "R1",
            "review_timestamp": "2026-09-05",
            "review_semantic_distinctness": "PASS",
            "review_implementation_leakage": "NONE"
        })

    auditor = HumanReviewAuditor(str(cand_path), str(csv_path))
    result = auditor.audit()
    assert result.is_complete is True
    assert result.is_freeze_eligible is True
    assert len(result.errors) == 0
    assert result.accept_count == 1
    assert result.total_cases == 1
