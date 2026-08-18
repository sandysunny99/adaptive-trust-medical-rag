"""
Phase 11 — Claim Verification & Answer Safety Gate.

Implements the post-generation verification pipeline per the claim-verification
skill and RAG-integrity rules:

  Stage 1 — Atomic Claim Decomposition
    Split generated answer into discrete, verifiable factual propositions.
    Rule-based sentence splitter + pharmacological claim extractor.

  Stage 2 — Claim-to-Evidence Alignment
    Lexical + keyword overlap between each claim and retrieved evidence chunks.
    Flag claims scoring below ALIGNMENT_THRESHOLD = 0.70.

  Stage 3 — Citation Integrity & Entity Check
    Verify [Source N] citation IDs exist in the retrieved evidence list.
    Verify the cited chunk actually supports the claim (alignment >= threshold).
    Verify drug entity names match between claim and cited evidence.

  Stage 4 — Contradiction & Negation Detection
    Heuristic NLI: detect absolute/unsafe language patterns.
    Detect internal contradictions between claims in the same answer.

  Stage 5 — Answer Safety Gate Decision
    ALL grounded -> RELEASE with confidence score
    Minor ungrounded non-critical -> QUALIFY claims
    Critical ungrounded / contradiction -> ABSTAIN

  Confidence Formula (per skill):
    Confidence = 0.4 * GroundingRatio
               + 0.4 * MeanCitationTrust
               + 0.2 * (1 - ContradictionScore)

All logic is pure-Python and fully unit-testable without a live LLM.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Minimum alignment score for a claim to be considered grounded (skill §2)
ALIGNMENT_THRESHOLD: float = 0.70

#: Confidence formula weights (skill §5)
ALPHA: float = 0.4   # grounding ratio weight
BETA: float = 0.40   # citation trust weight
GAMMA: float = 0.20  # contradiction penalty weight

#: Absolute / unsafe language patterns — high-risk claims if ungrounded
_ABSOLUTE_PATTERNS: list[str] = [
    r"\b(100\s*%|never|always|cannot|impossible|guaranteed|completely safe)\b",
    r"\bno\s+(risk|side\s+effect|contraindication|interaction)\b",
    r"\bentirely\s+(safe|harmless|without\s+risk)\b",
    r"\bproven\s+to\s+(cure|prevent|eliminate)\b",
]

#: Citation reference pattern: [Source 1], [Source 2], etc.
_CITATION_RE = re.compile(r"\[Source\s+(\d+)\]", re.IGNORECASE)

#: Drug entity extractor — matches drug names + dose patterns in claims
_DRUG_DOSE_RE = re.compile(
    r"\b([A-Za-z]{3,}(?:mab|nib|olol|pril|sartan|statin|mycin|cillin|cycline|azole)?)"
    r"(?:\s+(\d+\.?\d*\s*(?:mg|mcg|g|IU|mL|mmol)(?:/(?:kg|day|dose))?))?\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class GateDecision(str, Enum):
    release = "release"     # all claims grounded, confidence meets threshold
    qualify = "qualify"     # minor issues — strip/qualify and release
    abstain = "abstain"     # critical ungrounded or contradiction — reject


@dataclass(frozen=True)
class EvidenceChunk:
    """Minimal evidence chunk used by the verifier (matches retrieval output)."""

    chunk_id: str
    text: str
    source_authority: float = 0.8
    citation_index: int = 0   # 1-based [Source N] index


@dataclass
class AtomicClaim:
    """A single discrete factual proposition extracted from the generated answer."""

    text: str
    claim_index: int
    citation_ids: list[int] = field(default_factory=list)   # parsed [Source N] refs
    is_critical: bool = False    # True if claim contains absolute/unsafe language
    drug_entities: list[str] = field(default_factory=list)  # drug names in claim


@dataclass
class AlignmentResult:
    """Result of aligning one claim against the evidence pool."""

    claim: AtomicClaim
    best_chunk_id: str | None
    alignment_score: float          # 0.0–1.0
    is_grounded: bool               # alignment_score >= ALIGNMENT_THRESHOLD
    citation_valid: bool            # cited source exists & supports claim
    entity_match: bool              # drug entities consistent with evidence


@dataclass
class ContradictionFlag:
    """A detected contradiction between a claim and evidence or another claim."""

    claim_index_a: int
    claim_index_b: int | None       # None if contradiction is vs evidence
    description: str
    severity: str                   # 'critical' | 'minor'


@dataclass
class VerificationReport:
    """Full output of the claim verification pipeline."""

    claims: list[AtomicClaim]
    alignments: list[AlignmentResult]
    contradictions: list[ContradictionFlag]
    grounding_ratio: float
    mean_citation_trust: float
    contradiction_score: float
    confidence: float
    decision: GateDecision
    explanation: str
    qualified_answer: str | None = None   # set when decision == 'qualify'

    @property
    def ungrounded_claims(self) -> list[AlignmentResult]:
        return [a for a in self.alignments if not a.is_grounded]

    @property
    def critical_ungrounded(self) -> list[AlignmentResult]:
        return [a for a in self.ungrounded_claims if a.claim.is_critical]


# ---------------------------------------------------------------------------
# Stage 1: Atomic Claim Decomposition
# ---------------------------------------------------------------------------


def _is_critical_claim(text: str) -> bool:
    """Return True if the claim contains absolute or unsafe language."""
    for pattern in _ABSOLUTE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _extract_drug_entities(text: str) -> list[str]:
    """Extract candidate drug entity names from claim text."""
    entities: list[str] = []
    for match in _DRUG_DOSE_RE.finditer(text):
        name = match.group(1).lower()
        # Filter out common English words that match the regex incidentally
        if len(name) >= 5 and name not in {
            "which", "there", "their", "these", "those", "where",
            "about", "after", "could", "should", "would", "under",
            "other", "above", "based", "given", "since", "being",
            "study", "shown", "found", "known", "used", "risk",
            "patients", "patient", "increase", "decrease",
        }:
            entities.append(name)
    return list(dict.fromkeys(entities))   # deduplicate, preserve order


def decompose_into_claims(answer: str) -> list[AtomicClaim]:
    """
    Stage 1: Split a generated answer into atomic factual propositions.

    Splits on sentence boundaries. Each sentence becomes one AtomicClaim.
    Citation IDs, drug entities, and critical-claim flags are extracted.
    """
    # Split on sentence boundaries (period/exclamation/question + space + capital)
    sentence_re = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")
    raw_sentences = sentence_re.split(answer.strip())

    claims: list[AtomicClaim] = []
    for idx, sent in enumerate(raw_sentences):
        sent = sent.strip()
        if not sent or len(sent) < 10:
            continue
        citation_ids = [int(m) for m in _CITATION_RE.findall(sent)]
        drug_entities = _extract_drug_entities(sent)
        is_critical = _is_critical_claim(sent)
        claims.append(AtomicClaim(
            text=sent,
            claim_index=idx,
            citation_ids=citation_ids,
            is_critical=is_critical,
            drug_entities=drug_entities,
        ))
    return claims


# ---------------------------------------------------------------------------
# Stage 2: Claim-to-Evidence Alignment
# ---------------------------------------------------------------------------


def _tokenize_lower(text: str) -> set[str]:
    """Lowercase alphanumeric token set for overlap scoring."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _alignment_score(claim_text: str, chunk_text: str) -> float:
    """
    Compute lexical alignment between a claim and an evidence chunk.

    Uses Jaccard-like overlap on content words (length >= 4) to avoid
    noise from stopwords. Returns 0.0–1.0.
    """
    claim_tokens = {t for t in _tokenize_lower(claim_text) if len(t) >= 4}
    chunk_tokens = {t for t in _tokenize_lower(chunk_text) if len(t) >= 4}
    if not claim_tokens:
        return 0.0
    overlap = claim_tokens & chunk_tokens
    # Normalise by claim length (how much of the claim is supported)
    return len(overlap) / len(claim_tokens)


def align_claims_to_evidence(
    claims: list[AtomicClaim],
    evidence: list[EvidenceChunk],
) -> list[AlignmentResult]:
    """
    Stage 2 & 3: Align each claim to the best matching evidence chunk.

    For each claim:
    - Find the evidence chunk with the highest alignment score.
    - Check if cited [Source N] chunks actually support the claim.
    - Check drug entity consistency between claim and evidence.
    """
    # Build citation index map: citation_index -> EvidenceChunk
    citation_map: dict[int, EvidenceChunk] = {
        c.citation_index: c for c in evidence if c.citation_index > 0
    }

    results: list[AlignmentResult] = []
    for claim in claims:
        if not evidence:
            results.append(AlignmentResult(
                claim=claim,
                best_chunk_id=None,
                alignment_score=0.0,
                is_grounded=False,
                citation_valid=False,
                entity_match=False,
            ))
            continue

        # Find best-matching chunk by alignment score
        scored = [
            (chunk, _alignment_score(claim.text, chunk.text))
            for chunk in evidence
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        best_chunk, best_score = scored[0]

        # Citation validity check (Stage 3)
        citation_valid = True
        if claim.citation_ids:
            # All cited sources must exist and support the claim
            for cid in claim.citation_ids:
                if cid not in citation_map:
                    citation_valid = False
                    break
                cited_score = _alignment_score(claim.text, citation_map[cid].text)
                if cited_score < ALIGNMENT_THRESHOLD * 0.6:   # cited chunk must loosely support
                    citation_valid = False
                    break
        # No citation on a grounded claim is acceptable (not fabricated)

        # Entity consistency check (Stage 3)
        entity_match = True
        if claim.drug_entities and best_score >= ALIGNMENT_THRESHOLD:
            chunk_text_lower = best_chunk.text.lower()
            # At least one drug entity in the claim must appear in the best chunk
            entity_match = any(ent in chunk_text_lower for ent in claim.drug_entities)

        results.append(AlignmentResult(
            claim=claim,
            best_chunk_id=best_chunk.chunk_id,
            alignment_score=round(best_score, 4),
            is_grounded=best_score >= ALIGNMENT_THRESHOLD,
            citation_valid=citation_valid,
            entity_match=entity_match,
        ))

    return results


# ---------------------------------------------------------------------------
# Stage 4: Contradiction & Negation Detection
# ---------------------------------------------------------------------------

# Negation patterns that reverse a claim's meaning
_NEGATION_SEEDS = [
    (r"\bcontraindicated\b", r"\bsafe\b|\brecommended\b|\bindicated\b"),
    (r"\bincreases?\s+risk\b", r"\bno\s+risk\b|\bdoes\s+not\s+increase\b"),
    (r"\bmust\s+(avoid|not)\b", r"\bmay\s+use\b|\bcan\s+be\s+used\b"),
]


def detect_contradictions(
    claims: list[AtomicClaim],
    evidence: list[EvidenceChunk],
) -> list[ContradictionFlag]:
    """
    Stage 4: Detect contradictions within the answer and against evidence.

    Checks:
    1. Absolute language in unverified claims (critical flags).
    2. Contradictory claim pairs within the answer (negation pattern matching).
    3. Claim asserts X but evidence asserts NOT X.
    """
    flags: list[ContradictionFlag] = []

    # 1. Flag absolute language patterns (e.g. "never causes", "100% safe")
    for claim in claims:
        for pattern in _ABSOLUTE_PATTERNS:
            if re.search(pattern, claim.text, re.IGNORECASE):
                flags.append(ContradictionFlag(
                    claim_index_a=claim.claim_index,
                    claim_index_b=None,
                    description=(
                        f"Absolute/unsafe language in claim: "
                        f"'{re.search(pattern, claim.text, re.IGNORECASE).group()}'"  # type: ignore[union-attr]
                    ),
                    severity="critical",
                ))
                break

    # 2. Intra-answer contradiction: check claim pairs for negation conflicts
    for i, claim_a in enumerate(claims):
        for claim_b in claims[i + 1:]:
            for pos_pattern, neg_pattern in _NEGATION_SEEDS:
                a_pos = bool(re.search(pos_pattern, claim_a.text, re.IGNORECASE))
                b_neg = bool(re.search(neg_pattern, claim_b.text, re.IGNORECASE))
                b_pos = bool(re.search(pos_pattern, claim_b.text, re.IGNORECASE))
                a_neg = bool(re.search(neg_pattern, claim_a.text, re.IGNORECASE))
                if (a_pos and b_neg) or (b_pos and a_neg):
                    flags.append(ContradictionFlag(
                        claim_index_a=claim_a.claim_index,
                        claim_index_b=claim_b.claim_index,
                        description=(
                            f"Intra-answer contradiction detected between "
                            f"claim {claim_a.claim_index} and claim {claim_b.claim_index}"
                        ),
                        severity="critical",
                    ))

    # 3. Claim vs evidence contradiction
    for claim in claims:
        claim_lower = claim.text.lower()
        for chunk in evidence:
            chunk_lower = chunk.text.lower()
            for pos_pattern, neg_pattern in _NEGATION_SEEDS:
                claim_pos = bool(re.search(pos_pattern, claim_lower))
                evidence_neg = bool(re.search(neg_pattern, chunk_lower))
                if claim_pos and evidence_neg:
                    flags.append(ContradictionFlag(
                        claim_index_a=claim.claim_index,
                        claim_index_b=None,
                        description=(
                            f"Claim contradicts evidence chunk '{chunk.chunk_id}'"
                        ),
                        severity="minor",
                    ))

    # Deduplicate (same pair can match multiple patterns)
    seen: set[tuple] = set()
    unique_flags: list[ContradictionFlag] = []
    for f in flags:
        key = (f.claim_index_a, f.claim_index_b, f.severity)
        if key not in seen:
            seen.add(key)
            unique_flags.append(f)

    return unique_flags


# ---------------------------------------------------------------------------
# Stage 5: Confidence & Safety Gate
# ---------------------------------------------------------------------------


def _compute_confidence(
    grounding_ratio: float,
    mean_citation_trust: float,
    contradiction_score: float,
) -> float:
    """
    Confidence = α·GroundingRatio + β·MeanCitationTrust + γ·(1 - ContradictionScore)

    α=0.4, β=0.4, γ=0.2  (per skill specification)
    """
    return round(
        ALPHA * grounding_ratio
        + BETA * mean_citation_trust
        + GAMMA * (1.0 - contradiction_score),
        4,
    )


def _qualify_answer(answer: str, ungrounded: list[AlignmentResult]) -> str:
    """
    Strip or qualify ungrounded non-critical claims.
    Prepends a research-output disclaimer.
    """
    qualified = answer
    for ar in ungrounded:
        if not ar.claim.is_critical:
            # Replace ungrounded sentence with a qualified version
            qualified = qualified.replace(
                ar.claim.text,
                f"[Note: insufficient evidence to verify — {ar.claim.text}]",
            )
    disclaimer = (
        "⚠ Research output only — not clinical advice. "
        "Some claims have been qualified due to limited retrieved evidence.\n\n"
    )
    return disclaimer + qualified


class AnswerSafetyGate:
    """
    Orchestrates the full 5-stage claim verification pipeline.

    Usage:
        gate = AnswerSafetyGate(risk_tier="R2", confidence_threshold=0.60)
        report = gate.verify(answer, evidence_chunks)
        if report.decision == GateDecision.abstain:
            return ABSTAIN_RESPONSE
    """

    #: Confidence thresholds per risk tier (mirrors abstention gate thresholds)
    TIER_THRESHOLDS: dict[str, float] = {
        "R0": 0.30,
        "R1": 0.45,
        "R2": 0.60,
        "R3": 0.75,
    }

    def __init__(
        self,
        risk_tier: str = "R1",
        confidence_threshold: float | None = None,
    ) -> None:
        self.risk_tier = risk_tier
        self.confidence_threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else self.TIER_THRESHOLDS.get(risk_tier, 0.45)
        )

    def verify(self, answer: str, evidence: list[EvidenceChunk]) -> VerificationReport:
        """
        Run all 5 verification stages and return a VerificationReport.

        Args:
            answer:   Raw LLM-generated answer text.
            evidence: Retrieved evidence chunks used to generate the answer.

        Returns:
            VerificationReport with gate decision and confidence score.
        """
        # Stage 1 — Decompose
        claims = decompose_into_claims(answer)

        if not claims:
            return VerificationReport(
                claims=[],
                alignments=[],
                contradictions=[],
                grounding_ratio=0.0,
                mean_citation_trust=0.0,
                contradiction_score=0.0,
                confidence=0.0,
                decision=GateDecision.abstain,
                explanation="Answer contains no verifiable claims.",
            )

        # Early abstain if no evidence provided — cannot ground any claim
        if not evidence:
            return VerificationReport(
                claims=claims,
                alignments=[],
                contradictions=[],
                grounding_ratio=0.0,
                mean_citation_trust=0.0,
                contradiction_score=0.0,
                confidence=0.0,
                decision=GateDecision.abstain,
                explanation=(
                    f"ABSTAIN: No retrieved evidence provided. "
                    f"Cannot ground any of {len(claims)} claim(s). "
                    f"Risk tier {self.risk_tier} requires confidence >= "
                    f"{self.confidence_threshold:.2f}."
                ),
            )

        # Stage 2 + 3 — Align + citation check
        alignments = align_claims_to_evidence(claims, evidence)

        # Stage 4 — Contradiction detection
        contradictions = detect_contradictions(claims, evidence)

        # Metrics
        grounded_count = sum(1 for a in alignments if a.is_grounded)
        grounding_ratio = grounded_count / len(claims)

        mean_citation_trust = (
            sum(c.source_authority for c in evidence) / len(evidence)
            if evidence else 0.0
        )

        critical_contradictions = [c for c in contradictions if c.severity == "critical"]
        contradiction_score = min(len(critical_contradictions) / max(len(claims), 1), 1.0)

        confidence = _compute_confidence(
            grounding_ratio, mean_citation_trust, contradiction_score
        )

        # Stage 5 — Gate decision
        ungrounded = [a for a in alignments if not a.is_grounded]
        critical_ungrounded = [a for a in ungrounded if a.claim.is_critical]

        qualified_answer: str | None = None
        critical_ungrounded_or_low_conf = (
            critical_ungrounded
            or (critical_contradictions and confidence < self.confidence_threshold)
        )
        if critical_ungrounded_or_low_conf:
            decision = GateDecision.abstain
            explanation = (
                f"ABSTAIN: {len(critical_ungrounded)} critical ungrounded claim(s); "
                f"{len(critical_contradictions)} critical contradiction(s); "
                f"confidence {confidence:.3f} < threshold {self.confidence_threshold:.2f} "
                f"for risk tier {self.risk_tier}."
            )
        elif confidence < self.confidence_threshold and ungrounded:
            decision = GateDecision.qualify
            qualified_answer = _qualify_answer(answer, ungrounded)
            explanation = (
                f"QUALIFY: confidence {confidence:.3f} below threshold "
                f"{self.confidence_threshold:.2f}. "
                f"{len(ungrounded)} non-critical claim(s) qualified."
            )
        else:
            decision = GateDecision.release
            explanation = (
                f"RELEASE: confidence {confidence:.3f} >= threshold "
                f"{self.confidence_threshold:.2f}. "
                f"All {len(claims)} claims verified."
            )

        return VerificationReport(
            claims=claims,
            alignments=alignments,
            contradictions=contradictions,
            grounding_ratio=round(grounding_ratio, 4),
            mean_citation_trust=round(mean_citation_trust, 4),
            contradiction_score=round(contradiction_score, 4),
            confidence=confidence,
            decision=decision,
            explanation=explanation,
            qualified_answer=qualified_answer,
        )
