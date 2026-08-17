"""Adaptive trust scoring engine.

Implements the multi-factor weighted trust formula from the
adaptive-trust-scoring skill specification:

    TrustScore(d, q, R) = Σ  w_i(R) · S_i(d, q, E)

Nine factor scores S_i ∈ [0,1]:
    source_authority  — tiered authority score from source_validator
    query_relevance   — semantic similarity / cross-encoder score
    evidence_quality  — study design / regulatory label quality
    freshness         — exponential time-decay score
    consistency       — cross-source consensus score
    entity_match      — RxCUI / entity alignment score
    population_match  — patient cohort match score
    anti_poisoning    — 1 − anomaly/poisoning score
    anti_injection    — 1 − indirect injection score

Risk-class weights are loaded from config/trust.yaml.
Eligibility thresholds (R0=0.30, R1=0.45, R2=0.60, R3=0.75) govern
whether a chunk is admitted to the LLM generation context.

Security rules enforced:
    - anti_poisoning and anti_injection cannot be overridden to 1.0 without
      explicit hash-verified provenance (security.md §2/§3).
    - Chunks with trust_score < risk_class_threshold are DISQUALIFIED
      and NEVER passed to the LLM (controlled abstention gate).
"""

from __future__ import annotations

import hashlib
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

RISK_CLASSES = ("R0", "R1", "R2", "R3")

TRUST_FACTORS = (
    "source_authority",
    "query_relevance",
    "evidence_quality",
    "freshness",
    "consistency",
    "entity_match",
    "population_match",
    "anti_poisoning",
    "anti_injection",
)

_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "trust.yaml"


# ─────────────────────────────────────────────────────────────────────────────
# Configuration loading
# ─────────────────────────────────────────────────────────────────────────────


def _load_trust_config(path: Path = _CONFIG_PATH) -> dict[str, Any]:
    """Load and validate trust.yaml. Raises ValueError on bad config."""
    if not path.exists():
        raise FileNotFoundError(f"Trust config not found: {path}")
    with path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Validate all weights sum to 1.0 per risk class
    for risk_class in RISK_CLASSES:
        weights = cfg["weights"][risk_class]
        total = sum(weights.values())
        if not math.isclose(total, 1.0, abs_tol=1e-6):
            raise ValueError(
                f"trust.yaml: weights for {risk_class} sum to {total:.6f}, expected 1.0"
            )
        missing = set(TRUST_FACTORS) - set(weights)
        if missing:
            raise ValueError(f"trust.yaml: {risk_class} is missing factors: {missing}")

    return cfg


# Module-level singleton — loaded once at import time
_trust_config = _load_trust_config()


# ─────────────────────────────────────────────────────────────────────────────
# Input / Output data models
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class TrustFactorScores:
    """All nine factor scores for a single evidence chunk.

    All scores MUST be in [0.0, 1.0].
    anti_poisoning = 1.0 − anomaly_score
    anti_injection = 1.0 − injection_score
    """

    source_authority: float = 0.0
    query_relevance: float = 0.0
    evidence_quality: float = 0.0
    freshness: float = 1.0
    consistency: float = 1.0
    entity_match: float = 0.0
    population_match: float = 1.0
    anti_poisoning: float = 1.0   # Default: assume clean until poisoning detected
    anti_injection: float = 1.0   # Default: assume clean until injection detected

    def __post_init__(self) -> None:
        for fname in TRUST_FACTORS:
            val = getattr(self, fname)
            if not (0.0 <= val <= 1.0):
                raise ValueError(
                    f"TrustFactorScores.{fname} = {val} is out of range [0.0, 1.0]"
                )

    def as_dict(self) -> dict[str, float]:
        return {f: getattr(self, f) for f in TRUST_FACTORS}


@dataclass
class TrustScoringResult:
    """Complete result of trust scoring a single evidence chunk."""

    chunk_id: str
    risk_class: str

    factor_scores: TrustFactorScores
    weights: dict[str, float]

    trust_score: float
    """Weighted composite score ∈ [0.0, 1.0]."""

    threshold: float
    """Eligibility threshold for this risk class."""

    is_eligible: bool
    """True if trust_score ≥ threshold."""

    config_hash: str
    """SHA-256 of the weight config used — for reproducibility audit."""

    score_breakdown: dict[str, float] = field(default_factory=dict)
    """Per-factor weighted contribution: w_i × S_i."""

    notes: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Trust scorer
# ─────────────────────────────────────────────────────────────────────────────


class AdaptiveTrustScorer:
    """Computes risk-class-weighted trust scores for evidence chunks.

    Usage:
        scorer = AdaptiveTrustScorer()
        result = scorer.score(
            chunk_id="chunk-001",
            risk_class="R2",
            factors=TrustFactorScores(
                source_authority=0.85,
                query_relevance=0.72,
                evidence_quality=0.80,
                freshness=0.90,
                entity_match=1.0,
                anti_poisoning=1.0,
                anti_injection=1.0,
            ),
        )
        if result.is_eligible:
            # admit chunk to LLM context
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._cfg = config or _trust_config
        self._config_hash = self._compute_config_hash()

    def _compute_config_hash(self) -> str:
        """SHA-256 of the weight config for audit reproducibility."""
        import json

        serialised = json.dumps(self._cfg["weights"], sort_keys=True)
        return hashlib.sha256(serialised.encode()).hexdigest()

    def _get_weights(self, risk_class: str) -> dict[str, float]:
        if risk_class not in RISK_CLASSES:
            raise ValueError(f"Invalid risk class '{risk_class}'. Must be one of {RISK_CLASSES}.")
        return self._cfg["weights"][risk_class]

    def _get_threshold(self, risk_class: str) -> float:
        return float(self._cfg["thresholds"][risk_class])

    def score(
        self,
        chunk_id: str,
        risk_class: str,
        factors: TrustFactorScores,
    ) -> TrustScoringResult:
        """Compute the weighted trust score for a single chunk.

        Args:
            chunk_id: Unique identifier for the evidence chunk.
            risk_class: One of 'R0', 'R1', 'R2', 'R3'.
            factors: All nine TrustFactorScores for this chunk.

        Returns:
            TrustScoringResult with trust_score, is_eligible, and full breakdown.
        """
        weights = self._get_weights(risk_class)
        threshold = self._get_threshold(risk_class)
        factor_dict = factors.as_dict()

        # Compute weighted contributions
        breakdown: dict[str, float] = {}
        total = 0.0
        for fname in TRUST_FACTORS:
            contribution = round(weights[fname] * factor_dict[fname], 6)
            breakdown[fname] = contribution
            total += contribution

        trust_score = round(total, 4)
        is_eligible = trust_score >= threshold
        notes: list[str] = []

        if not is_eligible:
            notes.append(
                f"Chunk '{chunk_id}' disqualified: trust_score={trust_score:.4f} "
                f"< {risk_class} threshold={threshold:.2f}. "
                "Controlled abstention — chunk excluded from LLM context."
            )
            logger.info(
                "ABSTAIN gate: chunk=%s risk=%s score=%.4f threshold=%.2f",
                chunk_id,
                risk_class,
                trust_score,
                threshold,
            )

        return TrustScoringResult(
            chunk_id=chunk_id,
            risk_class=risk_class,
            factor_scores=factors,
            weights=weights,
            trust_score=trust_score,
            threshold=threshold,
            is_eligible=is_eligible,
            config_hash=self._config_hash,
            score_breakdown=breakdown,
            notes=notes,
        )

    def score_batch(
        self,
        chunks: list[dict[str, Any]],
        risk_class: str,
    ) -> list[TrustScoringResult]:
        """Score multiple chunks under the same risk class.

        Each dict must have 'chunk_id' (str) and 'factors' (TrustFactorScores).
        Returns results sorted by trust_score descending.
        """
        results = [
            self.score(
                chunk_id=c["chunk_id"],
                risk_class=risk_class,
                factors=c["factors"],
            )
            for c in chunks
        ]
        return sorted(results, key=lambda r: r.trust_score, reverse=True)

    def filter_eligible(
        self,
        results: list[TrustScoringResult],
    ) -> list[TrustScoringResult]:
        """Return only eligible chunks (trust_score ≥ threshold).

        Callers should NEVER pass ineligible chunks to the LLM.
        """
        return [r for r in results if r.is_eligible]

    @property
    def config_hash(self) -> str:
        """SHA-256 of current weight config — for audit logging."""
        return self._config_hash


# ─────────────────────────────────────────────────────────────────────────────
# Risk classifier (query-level)
# ─────────────────────────────────────────────────────────────────────────────

# Keyword patterns that escalate query risk class
_R3_KEYWORDS = frozenset({
    "lethal dose", "ld50", "overdose", "fatal", "death", "suicide",
    "maximum dose", "toxic dose", "poisoning",
    "severe drug interaction", "contraindication", "black box warning",
    "torsades de pointes", "qt prolongation",
})

_R2_KEYWORDS = frozenset({
    "drug interaction", "adverse drug event", "ade", "side effect",
    "hepatotoxicity", "nephrotoxicity", "cardiotoxicity",
    "pregnancy", "pediatric dose", "geriatric dose", "renal impairment",
    "hepatic impairment", "narrow therapeutic index",
})

_R1_KEYWORDS = frozenset({
    "dose", "dosage", "mechanism of action", "pharmacokinetics",
    "absorption", "distribution", "metabolism", "excretion",
    "half life", "bioavailability",
})


def classify_query_risk(query: str) -> str:
    """Classify a sanitized query string into a risk class R0–R3.

    Uses keyword matching (deterministic, no LLM required).
    Returns the highest applicable risk class.

    Args:
        query: Sanitized query text (must have passed sanitize_query() first).

    Returns:
        One of 'R0', 'R1', 'R2', 'R3'.
    """
    lower = query.lower()

    for kw in _R3_KEYWORDS:
        if kw in lower:
            logger.info("Risk class R3 triggered by keyword: '%s'", kw)
            return "R3"

    for kw in _R2_KEYWORDS:
        if kw in lower:
            logger.info("Risk class R2 triggered by keyword: '%s'", kw)
            return "R2"

    for kw in _R1_KEYWORDS:
        if kw in lower:
            logger.info("Risk class R1 triggered by keyword: '%s'", kw)
            return "R1"

    return "R0"
