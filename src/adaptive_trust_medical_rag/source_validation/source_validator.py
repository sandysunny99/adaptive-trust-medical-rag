"""Medical source authority tiering and freshness decay scoring.

Implements the medical-source-validation skill specification:

Authority Tiers (skill table):
    Tier 5 (score 1.00) — FDA DailyMed / EMA SmPC regulatory labels
    Tier 4 (score 0.85) — Cochrane, USPSTF, NICE, AHA/ACC guidelines
    Tier 3 (score 0.70) — NEJM, Lancet, JAMA, BMJ (peer-reviewed RCTs)
    Tier 2 (score 0.50) — Specialty journals, observational studies
    Tier 1 (score 0.30) — Preprints (bioRxiv, medRxiv) — high-risk quarantine
    Tier 0 (score 0.00) — Unverified web / forums — DISALLOWED

Freshness formula (exponential decay, half-life 5 years):
    FreshnessScore(t) = exp(−λ · max(0, t_curr − t_pub))
    where λ = ln(2) / half_life_days

Special overrides:
    - FDA safety communication / black-box warning within 180 days → freshness = 1.0
    - Superseded / retracted documents → trust_score = 0.0
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from enum import IntEnum

# ─────────────────────────────────────────────────────────────────────────────
# Authority tier definitions
# ─────────────────────────────────────────────────────────────────────────────


class AuthorityTier(IntEnum):
    """Numeric authority tier (higher = more authoritative)."""

    DISALLOWED = 0   # Unverified web / forums
    PREPRINT = 1     # bioRxiv, medRxiv
    OBSERVATIONAL = 2  # Specialty journals, case series
    PRIMARY = 3      # NEJM, Lancet, JAMA, BMJ
    GUIDELINE = 4    # Cochrane, USPSTF, NICE, AHA/ACC
    REGULATORY = 5   # FDA DailyMed, EMA SmPC


# Base authority scores from the skill specification
AUTHORITY_SCORES: dict[AuthorityTier, float] = {
    AuthorityTier.DISALLOWED: 0.00,
    AuthorityTier.PREPRINT: 0.30,
    AuthorityTier.OBSERVATIONAL: 0.50,
    AuthorityTier.PRIMARY: 0.70,
    AuthorityTier.GUIDELINE: 0.85,
    AuthorityTier.REGULATORY: 1.00,
}

# Domain → authority tier mapping (used for auto-classification)
DOMAIN_TIER_MAP: dict[str, AuthorityTier] = {
    # Tier 5 — Regulatory
    "dailymed.nlm.nih.gov": AuthorityTier.REGULATORY,
    "labels.fda.gov": AuthorityTier.REGULATORY,
    "accessdata.fda.gov": AuthorityTier.REGULATORY,
    "ema.europa.eu": AuthorityTier.REGULATORY,
    "who.int": AuthorityTier.REGULATORY,
    # Tier 4 — Guidelines / Systematic Reviews
    "cochranelibrary.com": AuthorityTier.GUIDELINE,
    "uspreventiveservicestaskforce.org": AuthorityTier.GUIDELINE,
    "nice.org.uk": AuthorityTier.GUIDELINE,
    "heart.org": AuthorityTier.GUIDELINE,
    "acc.org": AuthorityTier.GUIDELINE,
    "guidelines.gov": AuthorityTier.GUIDELINE,
    # Tier 3 — High-impact journals
    "nejm.org": AuthorityTier.PRIMARY,
    "thelancet.com": AuthorityTier.PRIMARY,
    "jamanetwork.com": AuthorityTier.PRIMARY,
    "bmj.com": AuthorityTier.PRIMARY,
    "annals.org": AuthorityTier.PRIMARY,
    "pubmed.ncbi.nlm.nih.gov": AuthorityTier.PRIMARY,  # PubMed = peer-reviewed default
    "ncbi.nlm.nih.gov": AuthorityTier.PRIMARY,
    # Tier 2 — Standard journals
    "journals.plos.org": AuthorityTier.OBSERVATIONAL,
    "mdpi.com": AuthorityTier.OBSERVATIONAL,
    # Tier 1 — Preprints
    "biorxiv.org": AuthorityTier.PREPRINT,
    "medrxiv.org": AuthorityTier.PREPRINT,
    # Tier 0 — Disallowed (web forums, non-peer-reviewed blogs)
    "reddit.com": AuthorityTier.DISALLOWED,
    "quora.com": AuthorityTier.DISALLOWED,
}


# ─────────────────────────────────────────────────────────────────────────────
# Freshness decay engine
# ─────────────────────────────────────────────────────────────────────────────

# Half-lives in days
HALF_LIFE_GENERAL_DAYS: int = 1825   # 5 years — general clinical literature
HALF_LIFE_FAST_EVOLVING_DAYS: int = 1095  # 3 years — pharmacology / ADE research

# Black-box / safety communication recency window
FDA_SAFETY_COMM_WINDOW_DAYS: int = 180


def _decay_constant(half_life_days: int) -> float:
    """λ = ln(2) / half_life (exponential decay constant)."""
    return math.log(2) / half_life_days


def calculate_freshness_score(
    publication_date: date | None,
    reference_date: date | None = None,
    fast_evolving: bool = False,
    is_fda_safety_communication: bool = False,
) -> float:
    """Compute exponential freshness decay score.

    Args:
        publication_date: Date the evidence was published.
        reference_date: Date to measure decay from (defaults to today UTC).
        fast_evolving: If True, use 3-year half-life instead of 5-year.
        is_fda_safety_communication: If True and published within 180 days,
            return 1.0 (black-box override).

    Returns:
        Float in [0.0, 1.0].  1.0 = maximally fresh, 0.0 = fully stale.
    """
    if publication_date is None:
        return 0.5  # Unknown date → conservative mid-point

    today = reference_date or datetime.now(tz=timezone.utc).date()
    age_days = (today - publication_date).days

    # Black-box / safety communication override
    if is_fda_safety_communication and 0 <= age_days <= FDA_SAFETY_COMM_WINDOW_DAYS:
        return 1.0

    # Older than today? Clamp negative age to 0
    age_days = max(0, age_days)

    half_life = HALF_LIFE_FAST_EVOLVING_DAYS if fast_evolving else HALF_LIFE_GENERAL_DAYS
    lam = _decay_constant(half_life)
    return round(math.exp(-lam * age_days), 4)


# ─────────────────────────────────────────────────────────────────────────────
# Source validator
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class SourceValidationResult:
    """Output of validating a single evidence source."""

    source_name: str
    url: str | None

    tier: AuthorityTier
    authority_score: float
    freshness_score: float

    is_allowed: bool
    """False for Tier 0 (disallowed) sources."""

    is_quarantined: bool = False
    """True for Tier 1 preprints used in High-Risk (R3) queries."""

    is_superseded: bool = False
    """True when a newer label/retraction exists — composite trust = 0.0."""

    composite_score: float = 0.0
    """Blended authority × freshness score (before trust weighting)."""

    notes: list[str] = field(default_factory=list)


class SourceValidator:
    """Validates evidence sources against authority tiers and freshness rules.

    Weights (configurable):
        authority_weight: Proportion of composite score from authority tier.
        freshness_weight: Proportion from freshness decay.
    """

    def __init__(
        self,
        authority_weight: float = 0.60,
        freshness_weight: float = 0.40,
        domain_tier_map: dict[str, AuthorityTier] | None = None,
    ) -> None:
        if not math.isclose(authority_weight + freshness_weight, 1.0, abs_tol=1e-6):
            raise ValueError(
                f"authority_weight + freshness_weight must equal 1.0, "
                f"got {authority_weight + freshness_weight}"
            )
        self._authority_weight = authority_weight
        self._freshness_weight = freshness_weight
        self._domain_map = domain_tier_map or DOMAIN_TIER_MAP

    def _classify_tier_from_url(self, url: str | None) -> AuthorityTier | None:
        """Attempt to classify source tier from URL domain."""
        if not url:
            return None
        lower = url.lower()
        for domain, tier in self._domain_map.items():
            if domain in lower:
                return tier
        return None

    def validate(
        self,
        source_name: str,
        tier: AuthorityTier | int,
        publication_date: date | None = None,
        url: str | None = None,
        fast_evolving: bool = False,
        is_fda_safety_communication: bool = False,
        is_superseded: bool = False,
        risk_class: int = 0,
    ) -> SourceValidationResult:
        """Validate a single evidence source.

        Args:
            source_name: Human-readable name of the source.
            tier: AuthorityTier enum value or integer 0–5.
            publication_date: Publication date for freshness calculation.
            url: Source URL for domain-based tier override.
            fast_evolving: Use faster decay (pharmacology literature).
            is_fda_safety_communication: Activates 180-day freshness override.
            is_superseded: Mark as retracted/superseded → composite = 0.0.
            risk_class: Query risk class (0–3) for quarantine decisions.

        Returns:
            SourceValidationResult with all scores and flags set.
        """
        tier = AuthorityTier(int(tier))
        notes: list[str] = []

        # URL-based tier override (auto-classify unknown sources)
        url_tier = self._classify_tier_from_url(url)
        if url_tier is not None and url_tier != tier:
            notes.append(
                f"Tier overridden from {tier.name}({tier}) "
                f"→ {url_tier.name}({url_tier}) via URL domain match."
            )
            tier = url_tier

        authority_score = AUTHORITY_SCORES[tier]
        is_allowed = tier != AuthorityTier.DISALLOWED

        # Freshness
        freshness_score = calculate_freshness_score(
            publication_date,
            fast_evolving=fast_evolving,
            is_fda_safety_communication=is_fda_safety_communication,
        )
        if is_fda_safety_communication:
            notes.append("FDA safety communication freshness override applied.")

        # Superseded / retracted override
        if is_superseded:
            notes.append("Document is superseded or retracted — composite trust set to 0.0.")

        # Preprint quarantine for High-Risk (R3) queries
        is_quarantined = tier == AuthorityTier.PREPRINT and risk_class >= 3
        if is_quarantined:
            notes.append(
                "Preprint (Tier 1) quarantined for R3 High-Risk query "
                "per medical-source-validation skill."
            )

        composite = (
            0.0
            if (is_superseded or not is_allowed or is_quarantined)
            else round(
                authority_score * self._authority_weight
                + freshness_score * self._freshness_weight,
                4,
            )
        )

        return SourceValidationResult(
            source_name=source_name,
            url=url,
            tier=tier,
            authority_score=authority_score,
            freshness_score=freshness_score,
            is_allowed=is_allowed,
            is_quarantined=is_quarantined,
            is_superseded=is_superseded,
            composite_score=composite,
            notes=notes,
        )

    def validate_batch(
        self,
        sources: list[dict],
        risk_class: int = 0,
    ) -> list[SourceValidationResult]:
        """Validate multiple sources. Each dict must have 'name' and 'tier'.

        Optional keys: url, publication_date, fast_evolving,
                       is_fda_safety_communication, is_superseded.
        """
        results = []
        for s in sources:
            results.append(
                self.validate(
                    source_name=s["name"],
                    tier=s["tier"],
                    publication_date=s.get("publication_date"),
                    url=s.get("url"),
                    fast_evolving=s.get("fast_evolving", False),
                    is_fda_safety_communication=s.get("is_fda_safety_communication", False),
                    is_superseded=s.get("is_superseded", False),
                    risk_class=risk_class,
                )
            )
        return results
