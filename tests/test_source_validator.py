"""Comprehensive tests for medical source validation.

Tests cover:
    - Authority tier scoring (all 6 tiers)
    - Freshness decay formula correctness
    - FDA safety communication override (180-day window)
    - Superseded / retracted document zeroing
    - Tier 0 (DISALLOWED) rejection
    - Preprint quarantine for R3 High-Risk queries
    - URL-based tier auto-classification
    - Composite score calculation (authority × weight + freshness × weight)
    - Weight validation (must sum to 1.0)
    - Batch validation
"""

from __future__ import annotations

import math
from datetime import date, timedelta

import pytest

from adaptive_trust_medical_rag.source_validation.source_validator import (
    AUTHORITY_SCORES,
    HALF_LIFE_FAST_EVOLVING_DAYS,
    HALF_LIFE_GENERAL_DAYS,
    AuthorityTier,
    SourceValidator,
    calculate_freshness_score,
)

# ─────────────────────────────────────────────────────────────────────────────
# Authority tier tests
# ─────────────────────────────────────────────────────────────────────────────


def test_authority_scores_match_spec() -> None:
    """All tier scores must match the skill specification table."""
    assert AUTHORITY_SCORES[AuthorityTier.DISALLOWED] == 0.00
    assert AUTHORITY_SCORES[AuthorityTier.PREPRINT] == 0.30
    assert AUTHORITY_SCORES[AuthorityTier.OBSERVATIONAL] == 0.50
    assert AUTHORITY_SCORES[AuthorityTier.PRIMARY] == 0.70
    assert AUTHORITY_SCORES[AuthorityTier.GUIDELINE] == 0.85
    assert AUTHORITY_SCORES[AuthorityTier.REGULATORY] == 1.00


def test_tier_ordering() -> None:
    """Higher tier must have higher authority score."""
    tiers = [
        AuthorityTier.DISALLOWED,
        AuthorityTier.PREPRINT,
        AuthorityTier.OBSERVATIONAL,
        AuthorityTier.PRIMARY,
        AuthorityTier.GUIDELINE,
        AuthorityTier.REGULATORY,
    ]
    scores = [AUTHORITY_SCORES[t] for t in tiers]
    assert scores == sorted(scores)


def test_regulatory_tier_score_is_one() -> None:
    result = SourceValidator().validate("FDA DailyMed", tier=AuthorityTier.REGULATORY)
    assert result.authority_score == 1.00
    assert result.is_allowed is True


def test_disallowed_tier_rejected() -> None:
    result = SourceValidator().validate("Reddit Health Forum", tier=AuthorityTier.DISALLOWED)
    assert result.is_allowed is False
    assert result.composite_score == 0.0
    assert result.authority_score == 0.00


# ─────────────────────────────────────────────────────────────────────────────
# Freshness decay tests
# ─────────────────────────────────────────────────────────────────────────────


def test_freshness_score_today_is_one() -> None:
    """Document published today should have freshness ≈ 1.0."""
    today = date.today()
    score = calculate_freshness_score(today, reference_date=today)
    assert math.isclose(score, 1.0, abs_tol=1e-4)


def test_freshness_score_at_half_life_general() -> None:
    """Score at exactly 5 years (general half-life) must be ≈ 0.5."""
    reference = date(2025, 1, 1)
    pub_date = reference - timedelta(days=HALF_LIFE_GENERAL_DAYS)
    score = calculate_freshness_score(pub_date, reference_date=reference)
    assert math.isclose(score, 0.5, abs_tol=0.01)


def test_freshness_score_at_half_life_fast() -> None:
    """Score at exactly 3 years (fast-evolving half-life) must be ≈ 0.5."""
    reference = date(2025, 1, 1)
    pub_date = reference - timedelta(days=HALF_LIFE_FAST_EVOLVING_DAYS)
    score = calculate_freshness_score(pub_date, reference_date=reference, fast_evolving=True)
    assert math.isclose(score, 0.5, abs_tol=0.01)


def test_freshness_score_monotonically_decreasing() -> None:
    """Older documents must have lower freshness scores."""
    reference = date(2025, 1, 1)
    scores = [
        calculate_freshness_score(
            reference - timedelta(days=d), reference_date=reference
        )
        for d in [0, 365, 730, 1825, 3650]
    ]
    assert scores == sorted(scores, reverse=True)


def test_freshness_unknown_date_returns_midpoint() -> None:
    """Unknown publication date should return conservative 0.5."""
    score = calculate_freshness_score(None)
    assert score == 0.5


def test_freshness_future_date_clamped_to_one() -> None:
    """Future publication date (pre-print deposit) should not exceed 1.0."""
    future = date.today() + timedelta(days=30)
    score = calculate_freshness_score(future)
    assert 0.0 <= score <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# FDA safety communication override
# ─────────────────────────────────────────────────────────────────────────────


def test_fda_safety_comm_within_180_days_freshness_is_one() -> None:
    reference = date(2025, 6, 1)
    pub = reference - timedelta(days=90)  # 90 days ago — within window
    score = calculate_freshness_score(
        pub, reference_date=reference, is_fda_safety_communication=True
    )
    assert score == 1.0


def test_fda_safety_comm_beyond_180_days_no_override() -> None:
    reference = date(2025, 6, 1)
    pub = reference - timedelta(days=200)  # 200 days ago — outside window
    score_override = calculate_freshness_score(
        pub, reference_date=reference, is_fda_safety_communication=True
    )
    score_normal = calculate_freshness_score(pub, reference_date=reference)
    # Beyond 180 days, override does NOT apply → scores are equal
    assert math.isclose(score_override, score_normal, abs_tol=1e-6)


# ─────────────────────────────────────────────────────────────────────────────
# Superseded / retracted tests
# ─────────────────────────────────────────────────────────────────────────────


def test_superseded_document_composite_is_zero() -> None:
    today = date.today()
    result = SourceValidator().validate(
        "Retracted Lancet Study",
        tier=AuthorityTier.PRIMARY,
        publication_date=today,
        is_superseded=True,
    )
    assert result.composite_score == 0.0
    assert result.is_superseded is True
    assert any("superseded" in n.lower() for n in result.notes)


# ─────────────────────────────────────────────────────────────────────────────
# Preprint quarantine for R3 High-Risk queries
# ─────────────────────────────────────────────────────────────────────────────


def test_preprint_quarantined_for_r3_query() -> None:
    result = SourceValidator().validate(
        "medRxiv preprint",
        tier=AuthorityTier.PREPRINT,
        publication_date=date.today(),
        risk_class=3,
    )
    assert result.is_quarantined is True
    assert result.composite_score == 0.0
    assert any("quarantined" in n.lower() for n in result.notes)


def test_preprint_not_quarantined_for_r1_query() -> None:
    result = SourceValidator().validate(
        "medRxiv preprint",
        tier=AuthorityTier.PREPRINT,
        publication_date=date.today(),
        risk_class=1,
    )
    assert result.is_quarantined is False
    assert result.composite_score > 0.0


# ─────────────────────────────────────────────────────────────────────────────
# URL-based auto-classification
# ─────────────────────────────────────────────────────────────────────────────


def test_url_overrides_tier_to_regulatory() -> None:
    """FDA DailyMed URL must escalate tier to REGULATORY."""
    result = SourceValidator().validate(
        "Drug Label",
        tier=AuthorityTier.OBSERVATIONAL,  # wrong tier supplied
        url="https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=abc",
        publication_date=date.today(),
    )
    assert result.tier == AuthorityTier.REGULATORY
    assert result.authority_score == 1.00
    assert any("overridden" in n.lower() for n in result.notes)


def test_url_overrides_tier_to_preprint() -> None:
    """bioRxiv URL must downgrade tier to PREPRINT."""
    result = SourceValidator().validate(
        "Preprint paper",
        tier=AuthorityTier.PRIMARY,  # wrong tier supplied
        url="https://www.biorxiv.org/content/10.1101/2024.01.01",
        publication_date=date.today(),
    )
    assert result.tier == AuthorityTier.PREPRINT
    assert result.authority_score == 0.30


def test_unknown_url_does_not_change_tier() -> None:
    result = SourceValidator().validate(
        "Unknown journal",
        tier=AuthorityTier.OBSERVATIONAL,
        url="https://www.unknownjournal.example.com/article/123",
        publication_date=date.today(),
    )
    assert result.tier == AuthorityTier.OBSERVATIONAL


# ─────────────────────────────────────────────────────────────────────────────
# Composite score calculation
# ─────────────────────────────────────────────────────────────────────────────


def test_composite_score_formula() -> None:
    """composite = authority × 0.60 + freshness × 0.40 for fresh regulatory source."""
    validator = SourceValidator(authority_weight=0.60, freshness_weight=0.40)
    result = validator.validate(
        "FDA Label",
        tier=AuthorityTier.REGULATORY,
        publication_date=date.today(),  # freshness ≈ 1.0
    )
    expected = round(1.0 * 0.60 + 1.0 * 0.40, 4)
    assert math.isclose(result.composite_score, expected, abs_tol=0.01)


def test_composite_score_old_preprint_low() -> None:
    """10-year-old preprint on a general topic should have a low composite.

    Actual value: authority(0.30) × 0.60 + freshness(≈0.20) × 0.40 ≈ 0.26
    The composite is dominated by the low authority tier (Tier 1 = 0.30).
    """
    old_date = date(2015, 1, 1)
    result = SourceValidator().validate(
        "Old preprint",
        tier=AuthorityTier.PREPRINT,
        publication_date=old_date,
        risk_class=1,
    )
    assert result.composite_score < 0.30  # well below any operational trust threshold


def test_invalid_weights_raise() -> None:
    with pytest.raises(ValueError, match="must equal 1.0"):
        SourceValidator(authority_weight=0.70, freshness_weight=0.70)


# ─────────────────────────────────────────────────────────────────────────────
# Batch validation
# ─────────────────────────────────────────────────────────────────────────────


def test_batch_validation_returns_correct_count() -> None:
    sources = [
        {"name": "FDA Label", "tier": AuthorityTier.REGULATORY, "publication_date": date.today()},
        {
            "name": "Cochrane Review",
            "tier": AuthorityTier.GUIDELINE,
            "publication_date": date.today(),
        },
        {"name": "Reddit Post", "tier": AuthorityTier.DISALLOWED},
    ]
    results = SourceValidator().validate_batch(sources, risk_class=1)
    assert len(results) == 3
    assert results[0].is_allowed is True
    assert results[2].is_allowed is False


def test_batch_all_disallowed_filtered() -> None:
    sources = [
        {"name": "Forum", "tier": AuthorityTier.DISALLOWED},
        {"name": "Blog", "tier": AuthorityTier.DISALLOWED},
    ]
    results = SourceValidator().validate_batch(sources)
    assert all(r.composite_score == 0.0 for r in results)
    assert all(not r.is_allowed for r in results)
