"""Comprehensive tests for the adaptive trust scoring engine.

Covers:
    - Weight loading and validation (config integrity)
    - Config hash determinism (audit reproducibility)
    - Weight sum correctness for all 4 risk classes
    - TrustFactorScores range validation
    - Trust score formula: weighted sum correctness
    - Eligibility gate: score < threshold → disqualified
    - R3 stricter threshold than R0
    - Batch scoring: sorted descending, filter_eligible
    - Risk classifier: R0/R1/R2/R3 keyword triggers
    - Anti-poisoning / anti-injection penalty propagation
    - All-max factors → score = 1.0
    - All-zero factors → score = 0.0 → not eligible
    - Score breakdown contributions sum equals trust_score
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from adaptive_trust_medical_rag.trust_scoring.trust_scorer import (
    RISK_CLASSES,
    TRUST_FACTORS,
    AdaptiveTrustScorer,
    TrustFactorScores,
    _load_trust_config,
    classify_query_risk,
)

# ─────────────────────────────────────────────────────────────────────────────
# Config loading & integrity
# ─────────────────────────────────────────────────────────────────────────────


def test_trust_config_loads_without_error() -> None:
    cfg = _load_trust_config()
    assert "weights" in cfg
    assert "thresholds" in cfg


def test_all_risk_classes_present_in_config() -> None:
    cfg = _load_trust_config()
    for rc in RISK_CLASSES:
        assert rc in cfg["weights"], f"Missing risk class {rc} in trust.yaml"
        assert rc in cfg["thresholds"], f"Missing threshold for {rc} in trust.yaml"


def test_weights_sum_to_one_for_all_risk_classes() -> None:
    """Every risk class weight vector must sum to exactly 1.0."""
    cfg = _load_trust_config()
    for rc in RISK_CLASSES:
        total = sum(cfg["weights"][rc].values())
        assert math.isclose(total, 1.0, abs_tol=1e-6), (
            f"{rc} weights sum to {total}, expected 1.0"
        )


def test_all_factors_present_in_every_risk_class() -> None:
    cfg = _load_trust_config()
    for rc in RISK_CLASSES:
        for factor in TRUST_FACTORS:
            assert factor in cfg["weights"][rc], f"Factor '{factor}' missing in {rc}"


def test_thresholds_match_spec() -> None:
    """Thresholds must exactly match AGENTS.md specification."""
    cfg = _load_trust_config()
    assert cfg["thresholds"]["R0"] == 0.30
    assert cfg["thresholds"]["R1"] == 0.45
    assert cfg["thresholds"]["R2"] == 0.60
    assert cfg["thresholds"]["R3"] == 0.75


def test_config_not_found_raises_file_not_found() -> None:
    with pytest.raises(FileNotFoundError):
        _load_trust_config(Path("/nonexistent/trust.yaml"))


def test_invalid_weights_config_raises_value_error(tmp_path: Path) -> None:
    bad_yaml = tmp_path / "trust.yaml"
    bad_yaml.write_text(
        "thresholds:\n  R0: 0.30\n  R1: 0.45\n  R2: 0.60\n  R3: 0.75\n"
        "weights:\n"
        "  R0:\n    source_authority: 0.99\n    query_relevance: 0.99\n"
        "    evidence_quality: 0.0\n    freshness: 0.0\n    consistency: 0.0\n"
        "    entity_match: 0.0\n    population_match: 0.0\n"
        "    anti_poisoning: 0.0\n    anti_injection: 0.0\n"
        "  R1:\n    source_authority: 0.20\n    query_relevance: 0.20\n"
        "    evidence_quality: 0.15\n    freshness: 0.10\n    consistency: 0.10\n"
        "    entity_match: 0.10\n    population_match: 0.05\n"
        "    anti_poisoning: 0.05\n    anti_injection: 0.05\n"
        "  R2:\n    source_authority: 0.25\n    query_relevance: 0.15\n"
        "    evidence_quality: 0.20\n    freshness: 0.10\n    consistency: 0.10\n"
        "    entity_match: 0.10\n    population_match: 0.05\n"
        "    anti_poisoning: 0.03\n    anti_injection: 0.02\n"
        "  R3:\n    source_authority: 0.30\n    query_relevance: 0.10\n"
        "    evidence_quality: 0.25\n    freshness: 0.10\n    consistency: 0.10\n"
        "    entity_match: 0.10\n    population_match: 0.03\n"
        "    anti_poisoning: 0.01\n    anti_injection: 0.01\n"
    )
    with pytest.raises(ValueError, match="sum to"):
        _load_trust_config(bad_yaml)


# ─────────────────────────────────────────────────────────────────────────────
# TrustFactorScores validation
# ─────────────────────────────────────────────────────────────────────────────


def test_factor_scores_valid_range() -> None:
    scores = TrustFactorScores(
        source_authority=1.0,
        query_relevance=0.5,
        evidence_quality=0.8,
        freshness=0.9,
        consistency=0.7,
        entity_match=1.0,
        population_match=0.6,
        anti_poisoning=1.0,
        anti_injection=1.0,
    )
    assert scores.source_authority == 1.0


def test_factor_score_out_of_range_raises() -> None:
    with pytest.raises(ValueError, match="out of range"):
        TrustFactorScores(source_authority=1.5)


def test_factor_score_negative_raises() -> None:
    with pytest.raises(ValueError, match="out of range"):
        TrustFactorScores(query_relevance=-0.1)


def test_factor_scores_as_dict_has_all_factors() -> None:
    scores = TrustFactorScores()
    d = scores.as_dict()
    assert set(d.keys()) == set(TRUST_FACTORS)


# ─────────────────────────────────────────────────────────────────────────────
# Trust scorer — formula correctness
# ─────────────────────────────────────────────────────────────────────────────


def test_all_max_factors_score_is_one() -> None:
    """If every factor = 1.0, trust_score must equal 1.0 (weights sum to 1)."""
    scorer = AdaptiveTrustScorer()
    for rc in RISK_CLASSES:
        factors = TrustFactorScores(
            source_authority=1.0,
            query_relevance=1.0,
            evidence_quality=1.0,
            freshness=1.0,
            consistency=1.0,
            entity_match=1.0,
            population_match=1.0,
            anti_poisoning=1.0,
            anti_injection=1.0,
        )
        result = scorer.score("chunk-max", rc, factors)
        assert math.isclose(result.trust_score, 1.0, abs_tol=1e-4), (
            f"{rc}: expected 1.0, got {result.trust_score}"
        )


def test_all_zero_factors_score_is_zero() -> None:
    """If every factor = 0.0, trust_score must be 0.0 and not eligible."""
    scorer = AdaptiveTrustScorer()
    for rc in RISK_CLASSES:
        factors = TrustFactorScores(
            source_authority=0.0,
            query_relevance=0.0,
            evidence_quality=0.0,
            freshness=0.0,
            consistency=0.0,
            entity_match=0.0,
            population_match=0.0,
            anti_poisoning=0.0,
            anti_injection=0.0,
        )
        result = scorer.score("chunk-zero", rc, factors)
        assert result.trust_score == 0.0
        assert result.is_eligible is False


def test_score_breakdown_sums_to_trust_score() -> None:
    """Sum of per-factor contributions must equal trust_score."""
    scorer = AdaptiveTrustScorer()
    factors = TrustFactorScores(
        source_authority=0.85,
        query_relevance=0.72,
        evidence_quality=0.80,
        freshness=0.90,
        consistency=0.65,
        entity_match=1.00,
        population_match=0.70,
        anti_poisoning=1.00,
        anti_injection=1.00,
    )
    result = scorer.score("chunk-A", "R2", factors)
    breakdown_sum = round(sum(result.score_breakdown.values()), 4)
    assert math.isclose(breakdown_sum, result.trust_score, abs_tol=1e-4)


def test_manual_r2_score_calculation() -> None:
    """Hand-verify the R2 trust score for known factor values."""
    cfg = _load_trust_config()
    w = cfg["weights"]["R2"]
    factors = TrustFactorScores(
        source_authority=0.70,   # Tier 3 (PRIMARY)
        query_relevance=0.80,
        evidence_quality=0.70,
        freshness=0.85,
        consistency=0.60,
        entity_match=1.00,
        population_match=0.50,
        anti_poisoning=1.00,
        anti_injection=1.00,
    )
    expected = sum(w[f] * getattr(factors, f) for f in TRUST_FACTORS)
    scorer = AdaptiveTrustScorer()
    result = scorer.score("chunk-manual", "R2", factors)
    assert math.isclose(result.trust_score, expected, abs_tol=1e-4)


# ─────────────────────────────────────────────────────────────────────────────
# Eligibility gate
# ─────────────────────────────────────────────────────────────────────────────


def test_r3_threshold_is_stricter_than_r0() -> None:
    """A score that passes R0 may fail R3."""
    scorer = AdaptiveTrustScorer()
    # Craft factors that produce a score around 0.40 (above R0=0.30, below R3=0.75)
    factors = TrustFactorScores(
        source_authority=0.30,
        query_relevance=0.40,
        evidence_quality=0.30,
        freshness=0.50,
        consistency=0.50,
        entity_match=0.40,
        population_match=0.50,
        anti_poisoning=0.50,
        anti_injection=0.50,
    )
    r0 = scorer.score("chunk-gate", "R0", factors)
    r3 = scorer.score("chunk-gate", "R3", factors)
    # R0 threshold is 0.30 — likely eligible; R3 threshold is 0.75 — likely not
    assert r3.threshold > r0.threshold


def test_ineligible_chunk_has_note() -> None:
    scorer = AdaptiveTrustScorer()
    factors = TrustFactorScores(
        source_authority=0.0,
        query_relevance=0.0,
        evidence_quality=0.0,
        freshness=0.0,
        consistency=0.0,
        entity_match=0.0,
        population_match=0.0,
        anti_poisoning=0.0,
        anti_injection=0.0,
    )
    result = scorer.score("chunk-bad", "R3", factors)
    assert not result.is_eligible
    assert len(result.notes) > 0
    assert "disqualified" in result.notes[0].lower()


def test_eligible_chunk_above_threshold() -> None:
    scorer = AdaptiveTrustScorer()
    factors = TrustFactorScores(
        source_authority=1.0,
        query_relevance=1.0,
        evidence_quality=1.0,
        freshness=1.0,
        consistency=1.0,
        entity_match=1.0,
        population_match=1.0,
        anti_poisoning=1.0,
        anti_injection=1.0,
    )
    result = scorer.score("chunk-good", "R3", factors)
    assert result.is_eligible is True
    assert result.trust_score >= result.threshold


# ─────────────────────────────────────────────────────────────────────────────
# Anti-poisoning / anti-injection penalty
# ─────────────────────────────────────────────────────────────────────────────


def test_poisoning_penalty_reduces_score() -> None:
    scorer = AdaptiveTrustScorer()
    clean = TrustFactorScores(
        source_authority=0.85, query_relevance=0.80, evidence_quality=0.80,
        freshness=0.90, consistency=0.80, entity_match=1.0,
        population_match=0.70, anti_poisoning=1.0, anti_injection=1.0,
    )
    poisoned = TrustFactorScores(
        source_authority=0.85, query_relevance=0.80, evidence_quality=0.80,
        freshness=0.90, consistency=0.80, entity_match=1.0,
        population_match=0.70, anti_poisoning=0.0, anti_injection=1.0,
    )
    clean_result = scorer.score("clean", "R1", clean)
    poisoned_result = scorer.score("poisoned", "R1", poisoned)
    assert poisoned_result.trust_score < clean_result.trust_score


def test_injection_penalty_reduces_score() -> None:
    scorer = AdaptiveTrustScorer()
    clean = TrustFactorScores(
        source_authority=0.85, query_relevance=0.80, evidence_quality=0.80,
        freshness=0.90, consistency=0.80, entity_match=1.0,
        population_match=0.70, anti_poisoning=1.0, anti_injection=1.0,
    )
    injected = TrustFactorScores(
        source_authority=0.85, query_relevance=0.80, evidence_quality=0.80,
        freshness=0.90, consistency=0.80, entity_match=1.0,
        population_match=0.70, anti_poisoning=1.0, anti_injection=0.0,
    )
    clean_r = scorer.score("clean", "R1", clean)
    injected_r = scorer.score("injected", "R1", injected)
    assert injected_r.trust_score < clean_r.trust_score


# ─────────────────────────────────────────────────────────────────────────────
# Batch scoring
# ─────────────────────────────────────────────────────────────────────────────


def test_batch_returns_sorted_descending() -> None:
    scorer = AdaptiveTrustScorer()
    chunks = [
        {
            "chunk_id": "low",
            "factors": TrustFactorScores(
                source_authority=0.30, query_relevance=0.30, evidence_quality=0.30,
                freshness=0.30, consistency=0.30, entity_match=0.30,
                population_match=0.30, anti_poisoning=0.30, anti_injection=0.30,
            ),
        },
        {
            "chunk_id": "high",
            "factors": TrustFactorScores(
                source_authority=1.0, query_relevance=1.0, evidence_quality=1.0,
                freshness=1.0, consistency=1.0, entity_match=1.0,
                population_match=1.0, anti_poisoning=1.0, anti_injection=1.0,
            ),
        },
        {
            "chunk_id": "mid",
            "factors": TrustFactorScores(
                source_authority=0.70, query_relevance=0.70, evidence_quality=0.70,
                freshness=0.70, consistency=0.70, entity_match=0.70,
                population_match=0.70, anti_poisoning=0.70, anti_injection=0.70,
            ),
        },
    ]
    results = scorer.score_batch(chunks, risk_class="R1")
    scores = [r.trust_score for r in results]
    assert scores == sorted(scores, reverse=True)
    assert results[0].chunk_id == "high"
    assert results[-1].chunk_id == "low"


def test_filter_eligible_removes_low_scoring_chunks() -> None:
    scorer = AdaptiveTrustScorer()
    chunks = [
        {
            "chunk_id": "pass",
            "factors": TrustFactorScores(
                source_authority=1.0, query_relevance=1.0, evidence_quality=1.0,
                freshness=1.0, consistency=1.0, entity_match=1.0,
                population_match=1.0, anti_poisoning=1.0, anti_injection=1.0,
            ),
        },
        {
            "chunk_id": "fail",
            "factors": TrustFactorScores(
                source_authority=0.0, query_relevance=0.0, evidence_quality=0.0,
                freshness=0.0, consistency=0.0, entity_match=0.0,
                population_match=0.0, anti_poisoning=0.0, anti_injection=0.0,
            ),
        },
    ]
    results = scorer.score_batch(chunks, risk_class="R3")
    eligible = scorer.filter_eligible(results)
    assert len(eligible) == 1
    assert eligible[0].chunk_id == "pass"


# ─────────────────────────────────────────────────────────────────────────────
# Config hash determinism
# ─────────────────────────────────────────────────────────────────────────────


def test_config_hash_is_deterministic() -> None:
    scorer1 = AdaptiveTrustScorer()
    scorer2 = AdaptiveTrustScorer()
    assert scorer1.config_hash == scorer2.config_hash


def test_config_hash_is_64_hex_chars() -> None:
    scorer = AdaptiveTrustScorer()
    assert len(scorer.config_hash) == 64
    assert all(c in "0123456789abcdef" for c in scorer.config_hash)


def test_result_contains_config_hash() -> None:
    scorer = AdaptiveTrustScorer()
    result = scorer.score("c1", "R0", TrustFactorScores())
    assert result.config_hash == scorer.config_hash


# ─────────────────────────────────────────────────────────────────────────────
# Risk classifier
# ─────────────────────────────────────────────────────────────────────────────


def test_classify_r3_lethal_dose() -> None:
    assert classify_query_risk("What is the lethal dose of digoxin?") == "R3"


def test_classify_r3_contraindication() -> None:
    assert classify_query_risk("warfarin contraindication with aspirin") == "R3"


def test_classify_r3_black_box_warning() -> None:
    assert classify_query_risk("Does methotrexate have a black box warning?") == "R3"


def test_classify_r2_drug_interaction() -> None:
    assert classify_query_risk("drug interaction between warfarin and ibuprofen") == "R2"


def test_classify_r2_adverse_event() -> None:
    assert classify_query_risk("adverse drug event profile of atorvastatin") == "R2"


def test_classify_r2_pregnancy() -> None:
    assert classify_query_risk("Is lisinopril safe during pregnancy?") == "R2"


def test_classify_r1_mechanism_of_action() -> None:
    assert classify_query_risk("mechanism of action of metoprolol") == "R1"


def test_classify_r1_pharmacokinetics() -> None:
    assert classify_query_risk("pharmacokinetics of omeprazole") == "R1"


def test_classify_r0_general_info() -> None:
    assert classify_query_risk("What is warfarin used for?") == "R0"


def test_classify_r0_empty_query() -> None:
    assert classify_query_risk("") == "R0"


def test_invalid_risk_class_raises() -> None:
    scorer = AdaptiveTrustScorer()
    with pytest.raises(ValueError, match="Invalid risk class"):
        scorer.score("c", "R9", TrustFactorScores())
