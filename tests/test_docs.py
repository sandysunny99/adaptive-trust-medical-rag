"""
Tests for Phase 24 - Documentation Integrity & Research Artifacts (test_docs.py).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


@pytest.fixture
def readme_path() -> Path:
    return Path("README.md")


@pytest.fixture
def architecture_path() -> Path:
    return Path("docs/ARCHITECTURE.md")


class TestReadmeIntegrity:
    def test_readme_exists_and_non_empty(self, readme_path: Path) -> None:
        assert readme_path.exists()
        assert readme_path.stat().st_size > 1000

    def test_readme_contains_core_sections(self, readme_path: Path) -> None:
        content = readme_path.read_text(encoding="utf-8")

        required_sections = [
            "Research Question",
            "Architecture & Dual Safety Gates",
            "Ablation Study Variants",
            "Security & Threat Model",
            "Installation & Setup",
            "Command Line Interface (CLI) Usage",
            "FastAPI REST API",
            "Experimental Evaluation Scorecard",
            "License & Attestation",
        ]
        for sec in required_sections:
            assert sec in content, f"Missing section in README.md: {sec}"

    def test_readme_contains_all_ablation_variants(self, readme_path: Path) -> None:
        content = readme_path.read_text(encoding="utf-8")
        variants = [
            "Vanilla LLM",
            "Standard Semantic RAG",
            "Hybrid RAG",
            "Entity-Attributed RAG",
            "Trust-Scored RAG",
            "Full Architecture",
        ]
        for var in variants:
            assert var in content, f"Missing variant in README.md: {var}"

    def test_readme_contains_disclaimer(self, readme_path: Path) -> None:
        content = readme_path.read_text(encoding="utf-8")
        assert "NOT an FDA-approved" in content or "Non-Clinical Disclaimer" in content

    def test_readme_cli_examples_present(self, readme_path: Path) -> None:
        content = readme_path.read_text(encoding="utf-8")
        assert "medical-rag query" in content
        assert "medical-rag ingest" in content
        assert "medical-rag eval" in content
        assert "medical-rag report" in content
        assert "medical-rag db" in content
        assert "medical-rag health" in content


class TestArchitectureDocIntegrity:
    def test_architecture_doc_exists_and_non_empty(self, architecture_path: Path) -> None:
        assert architecture_path.exists()
        assert architecture_path.stat().st_size > 1000

    def test_architecture_doc_contains_key_topics(self, architecture_path: Path) -> None:
        content = architecture_path.read_text(encoding="utf-8")

        required_topics = [
            "Evidence Eligibility Gate",
            "Answer Safety Gate",
            "Source Authority Score",
            "Freshness Score",
            "Multi-Factor Trust Score Calculation",
            "Database Entity-Relationship Schema",
            "Threat Model & Security Mitigations",
            "Research Integrity Policy",
        ]
        for topic in required_topics:
            assert topic in content, f"Missing topic in docs/ARCHITECTURE.md: {topic}"

    def test_architecture_doc_risk_thresholds(self, architecture_path: Path) -> None:
        content = architecture_path.read_text(encoding="utf-8")
        assert "0.30" in content
        assert "0.45" in content
        assert "0.60" in content
        assert "0.75" in content


class TestDocsSecurityProperties:
    def test_no_hardcoded_passwords_or_tokens_in_docs(
        self, readme_path: Path, architecture_path: Path
    ) -> None:
        for path in [readme_path, architecture_path]:
            content = path.read_text(encoding="utf-8")
            # Check for GitHub tokens
            assert not re.search(r"ghp_[A-Za-z0-9]{36}", content)
            # Check for SSN pattern
            assert not re.search(r"\d{3}-\d{2}-\d{4}", content)
