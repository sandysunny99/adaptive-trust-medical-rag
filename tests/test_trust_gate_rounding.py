"""AUD-07 of the 2026-10-26 full-system audit (reports/MEDICAL_RAG_FULL_SYSTEM_AUDIT_2026-10-26.md):
the eligibility gate compares the unrounded trust score, so display rounding never lifts a score
just below a risk tier's threshold into eligibility. Expected values are computed by hand from
config/trust.yaml (every factor equal to x gives a score of x, because each tier's weights sum to 1).
"""

from adaptive_trust_medical_rag.trust_scoring.trust_scorer import AdaptiveTrustScorer, TrustFactorScores


def test_score_just_below_threshold_is_not_eligible_after_rounding():
    # Every factor 0.59996 gives a raw R2 score of 0.59996; it displays as 0.6 at 4 decimals.
    factors = TrustFactorScores(**{f: 0.59996 for f in TrustFactorScores().as_dict()})
    result = AdaptiveTrustScorer().score("aud07", "R2", factors)
    assert result.trust_score == 0.6
    assert result.threshold == 0.60
    assert result.is_eligible is False


def test_score_exactly_at_threshold_stays_eligible():
    factors = TrustFactorScores(**{f: 0.6 for f in TrustFactorScores().as_dict()})
    result = AdaptiveTrustScorer().score("aud07-eq", "R2", factors)
    assert result.is_eligible is True
    for tier, value in (("R0", 0.30), ("R1", 0.45), ("R3", 0.75)):
        at = TrustFactorScores(**{f: value for f in TrustFactorScores().as_dict()})
        assert AdaptiveTrustScorer().score("aud07-" + tier, tier, at).is_eligible is True
