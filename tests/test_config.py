"""Unit tests for Settings and trust threshold configuration."""

from __future__ import annotations

import os

import pytest


def test_trust_thresholds_defaults() -> None:
    """Trust thresholds should match AGENTS.md spec when no .env file is present."""
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    from adaptive_trust_medical_rag.core.config import Settings

    s = Settings()
    assert s.trust_threshold_r0 == 0.30
    assert s.trust_threshold_r1 == 0.45
    assert s.trust_threshold_r2 == 0.60
    assert s.trust_threshold_r3 == 0.75


def test_trust_threshold_by_risk_class() -> None:
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    from adaptive_trust_medical_rag.core.config import Settings

    s = Settings()
    assert s.trust_threshold(0) == 0.30
    assert s.trust_threshold(3) == 0.75


def test_invalid_risk_class_raises() -> None:
    os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    from adaptive_trust_medical_rag.core.config import Settings

    s = Settings()
    with pytest.raises(ValueError, match="Invalid risk class"):
        s.trust_threshold(4)
