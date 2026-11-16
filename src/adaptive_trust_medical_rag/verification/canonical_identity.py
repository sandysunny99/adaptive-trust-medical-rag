"""Canonical Relationship Identity for deterministic drug-pair binding.

Provides an explicit structural identity (subject RxCUI + object RxCUI + predicate + direction)
that complements textual NLI by enforcing deterministic entity/predicate/direction matching.

This control does not replace NLI â€” it adds a deterministic identity constraint.
It does not guarantee clinical correctness; it verifies identity consistency between
canonical evidence relationships and generated claim relationships.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from adaptive_trust_medical_rag.normalization.medication_lexicon import MedicationLexicon


class CanonicalDirection(str, Enum):
    """Directional semantics for a drug-drug relationship."""
    A_TO_B = "A_TO_B"
    B_TO_A = "B_TO_A"
    BIDIRECTIONAL = "BIDIRECTIONAL"
    UNKNOWN = "UNKNOWN"


class CanonicalMatchStatus(str, Enum):
    """Result of comparing source identity against claim identity."""
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    AMBIGUOUS = "AMBIGUOUS"
    UNAVAILABLE = "UNAVAILABLE"


# Bounded predicate set derived from existing RG-02 relationship extraction
# Do NOT invent new pharmacological ontology terms.
NORMALIZED_PREDICATES = {
    "interaction": "INTERACTION",
    "interacts": "INTERACTION",
    "inhibits": "INHIBITION",
    "inhibit": "INHIBITION",
    "inhibitor": "INHIBITION",
    "inhibition": "INHIBITION",
    "induces": "INDUCTION",
    "induce": "INDUCTION",
    "inducer": "INDUCTION",
    "induction": "INDUCTION",
    "increases": "INCREASES",
    "increase": "INCREASES",
    "increases exposure": "INCREASES",
    "decreases": "DECREASES",
    "decrease": "DECREASES",
    "reduces": "DECREASES",
    "reduces clearance": "DECREASES",
    "contraindicated": "CONTRAINDICATION",
    "contraindication": "CONTRAINDICATION",
    "potentiates": "POTENTIATION",
    "potentiation": "POTENTIATION",
    "antagonizes": "ANTAGONISM",
    "antagonism": "ANTAGONISM",
}


@dataclass(frozen=True)
class CanonicalRelationshipIdentity:
    """Structural identity of a pharmacological relationship.
    
    This is an IDENTITY object, not a trust/confidence/score object.
    Identity fields define WHAT relationship is being discussed.
    The provenance_chunk_id traces WHERE this identity was established.
    """
    subject_rxcui: str
    object_rxcui: str
    predicate: str
    direction: CanonicalDirection
    provenance_chunk_id: str | None = None


def normalize_predicate(raw: str) -> str:
    """Map a raw relationship string to a normalized predicate.
    
    Returns the normalized predicate if found in the bounded set,
    otherwise returns the raw string uppercased.
    """
    lowered = raw.strip().lower()
    return NORMALIZED_PREDICATES.get(lowered, raw.strip().upper())


def compare_identity(
    source: CanonicalRelationshipIdentity | None,
    claim: CanonicalRelationshipIdentity | None,
) -> tuple[CanonicalMatchStatus, str]:
    """Deterministic exact identity comparison.
    
    Returns (status, reason).
    
    Rules:
    - Both must be non-None and fully resolved.
    - All four identity fields (subject, object, predicate, direction) must match exactly.
    - Fuzzy/embedding/NLI similarity is prohibited for this comparison.
    - If either identity is None or has UNKNOWN direction, result is UNAVAILABLE.
    """
    if source is None:
        return CanonicalMatchStatus.UNAVAILABLE, "Source canonical identity not available"
    if claim is None:
        return CanonicalMatchStatus.UNAVAILABLE, "Claim canonical identity not resolved"

    if not source.subject_rxcui or not source.object_rxcui:
        return CanonicalMatchStatus.UNAVAILABLE, "Source identity has unresolved RxCUI"
    if not claim.subject_rxcui or not claim.object_rxcui:
        return CanonicalMatchStatus.AMBIGUOUS, "Claim identity has unresolved RxCUI"

    if source.direction == CanonicalDirection.UNKNOWN:
        return CanonicalMatchStatus.AMBIGUOUS, "Source direction is unknown"
    if claim.direction == CanonicalDirection.UNKNOWN:
        return CanonicalMatchStatus.AMBIGUOUS, "Claim direction is unknown"

    if source.subject_rxcui != claim.subject_rxcui:
        return CanonicalMatchStatus.MISMATCH, f"Subject RxCUI mismatch: source={source.subject_rxcui} claim={claim.subject_rxcui}"
    if source.object_rxcui != claim.object_rxcui:
        return CanonicalMatchStatus.MISMATCH, f"Object RxCUI mismatch: source={source.object_rxcui} claim={claim.object_rxcui}"
    if source.predicate != claim.predicate:
        return CanonicalMatchStatus.MISMATCH, f"Predicate mismatch: source={source.predicate} claim={claim.predicate}"
    if source.direction != claim.direction:
        return CanonicalMatchStatus.MISMATCH, f"Direction mismatch: source={source.direction.value} claim={claim.direction.value}"

    return CanonicalMatchStatus.MATCH, "All identity fields match"


# Simple drug entity extraction for claim parsing (reuses existing project patterns)
# Matches both suffix-based drug names (e.g. atorvastatin) and known exact names.
_KNOWN_DRUGS = (
    r"warfarin|metformin|aspirin|insulin|heparin|clopidogrel|"
    r"atorvastatin|simvastatin|lisinopril|omeprazole|ibuprofen|naproxen|"
    r"fluoxetine|sertraline|amiodarone|digoxin|phenytoin|carbamazepine|"
    r"rifampin|ketoconazole|erythromycin|clarithromycin|verapamil|diltiazem"
)
_SUFFIX_PATTERN = (
    r"[A-Za-z]{3,}(?:mab|nib|olol|pril|sartan|statin|mycin|cillin|cycline|azole)"
)
_DRUG_PATTERN = re.compile(
    r"\b(?:" + _KNOWN_DRUGS + r"|" + _SUFFIX_PATTERN + r")\b",
    re.IGNORECASE,
)

_PREDICATE_PATTERN = re.compile(
    r"\b(inhibits?|induces?|increases?|decreases?|reduces?|potentiates?|antagonizes?|interacts?|contraindicated)\b",
    re.IGNORECASE,
)


# "increases the risk of", "raise the risk of", "increase hyperkalemia risk": a change in an effect's risk.
_RISK_OF_EFFECT = re.compile(
    r"\b(?:increase[sd]?|decrease[sd]?|reduce[sd]?|raise[sd]?|lower(?:s|ed)?)\s+(?:the\s+)?(?:[\w-]+\s+){0,2}?risks?\b",
    re.IGNORECASE,
)


class RequestDrugMap(dict):
    """A drug name -> RxCUI map whose names are also recognised as drug mentions in claims.

    The fixed drug pattern does not know every medication (spironolactone, for example), so a
    claim naming one could never be given an identity. The live application passes the request's
    normalised names in this map; a plain dict (every research caller) keeps the fixed pattern only,
    so research results do not change.
    """


def drug_mentions(claim_text: str, drug_rxcui_map: dict[str, str]) -> list[str]:
    """Drug mentions in text order: the fixed pattern, plus a RequestDrugMap's own names."""
    pattern = _DRUG_PATTERN
    if isinstance(drug_rxcui_map, RequestDrugMap):
        names = sorted((n for n in drug_rxcui_map if n and n.strip()), key=len, reverse=True)
        if names:
            # Longer names first, so a name is never matched by a shorter one it contains.
            pattern = re.compile(
                r"\b(?:" + "|".join(re.escape(n) for n in names) + r"|" + _KNOWN_DRUGS + r"|" + _SUFFIX_PATTERN + r")\b",
                re.IGNORECASE,
            )
    return list(dict.fromkeys(m.lower() for m in pattern.findall(claim_text)))


_SOURCE_MARKER = re.compile(r"\[Source\s+\d+\]", re.IGNORECASE)
_TOKEN = re.compile(r"[^\W_]+")


def _folded_tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text)]


def _named_in(tokens: list[str], sources: list[list[str]]) -> bool:
    n = len(tokens)
    return any(src[i:i + n] == tokens for src in sources for i in range(len(src) - n + 1))


def medication_findings(statement: str, drug_rxcui_map: RequestDrugMap, cited_texts: list[str],
                        lexicon: MedicationLexicon) -> list[dict]:
    """Each medication the statement names, with its identity and whether a cited source names it.

    Mentions come from the pinned RxNorm lexicon and from drug_mentions (the request's names, a fixed list and
    drug-name suffixes), merged by text. ``status`` is "confirmed" (a medication of this analysis, by name or
    RxCUI), "unconfirmed" (a resolved RxNorm concept the analysis did not confirm) or "unresolved" (a suffix
    match absent from the lexicon, or an ambiguous span).
    """
    text = _SOURCE_MARKER.sub(" ", statement)
    sources = [_folded_tokens(t) for t in cited_texts]
    confirmed_rxcuis = set(drug_rxcui_map.values())
    findings: dict[tuple[str, ...], dict] = {}
    for m in lexicon.mentions(text):
        findings.setdefault(tuple(_folded_tokens(m.text)), {
            "text": m.text, "rxcui": m.rxcui, "rxnorm_name": m.name, "tty": m.tty,
            "status": "unresolved" if m.ambiguous else (
                "confirmed" if m.text.lower() in drug_rxcui_map or m.rxcui in confirmed_rxcuis else "unconfirmed")})
    for name in drug_mentions(text, drug_rxcui_map):
        findings.setdefault(tuple(_folded_tokens(name)), {
            "text": name, "rxcui": drug_rxcui_map.get(name), "rxnorm_name": None, "tty": None,
            "status": "confirmed" if name in drug_rxcui_map else "unresolved"})
    for key, f in findings.items():
        f["named_by_cited_source"] = _named_in(list(key), sources)
    return list(findings.values())


def medication_identity_violation(statement: str, drug_rxcui_map: RequestDrugMap, cited_texts: list[str],
                                  lexicon: MedicationLexicon | None) -> str | None:
    """Why the statement names a medication its cited sources do not name, or None.

    The pair identity check runs only for statements naming two or more drugs, so "Enalapril can cause
    hyperkalemia" cited to the lisinopril label (round-5 probe P01) and "Furosemide can cause hyperkalemia" cited to
    its diuretics section (probe P06) had no identity check. Every medication a statement names must be named by a
    cited source's text or title, whatever its status: a confirmed drug the source does not name is attributed to
    the wrong evidence; an unconfirmed one ("potassium", "spironolactone" in a lisinopril section) is allowed only
    as the source's own context. Exact names: a brand is not its generic's label, a salt not its base.
    Without a verified lexicon (``None``) no statement can be checked, so every one fails.

    shortcut: a name outside the lexicon and the drug-name suffixes (foreign, withdrawn or invented) is not seen.
    """
    if lexicon is None:
        return "medication lexicon unavailable, so medication identity cannot be checked"
    ungrounded = [f for f in medication_findings(statement, drug_rxcui_map, cited_texts, lexicon)
                  if not f["named_by_cited_source"]]
    for status, reason in (("unresolved", "names a medication whose identity could not be resolved: "),
                           ("unconfirmed", "names a medication this analysis did not confirm: "),
                           ("confirmed", "names a medication its cited sources do not mention: ")):
        names = [f["text"] for f in ungrounded if f["status"] == status]
        if names:
            return reason + ", ".join(names)
    return None


def extract_claim_identity(
    claim_text: str,
    drug_rxcui_map: dict[str, str],
) -> CanonicalRelationshipIdentity | None:
    """Attempt deterministic extraction of canonical identity from claim text.
    
    Uses regex-based entity and predicate extraction (no LLM parser).
    Returns None if extraction cannot resolve all required fields.
    
    Args:
        claim_text: The generated claim text.
        drug_rxcui_map: Mapping of lowercased drug name -> RxCUI (from DrugNormalizer).
    """
    # Deduplicate while preserving text-order (first occurrence wins)
    drugs_found = drug_mentions(claim_text, drug_rxcui_map)
    predicates_found = _PREDICATE_PATTERN.findall(claim_text)
    if isinstance(drug_rxcui_map, RequestDrugMap):
        # Live claims only (see RequestDrugMap): "increase the risk of <effect>" says the two drugs
        # together raise an effect's risk, not that one drug raises the other, so it names an
        # interaction. Predicates inside such a phrase are dropped; research callers are unchanged.
        risk_spans = [m.span() for m in _RISK_OF_EFFECT.finditer(claim_text)]
        predicates_found = [m.group(1) for m in _PREDICATE_PATTERN.finditer(claim_text)
                            if not any(s <= m.start() < e for s, e in risk_spans)]
        if not predicates_found and risk_spans:
            predicates_found = ["interaction"]

    if len(drugs_found) < 2 or not predicates_found:
        return None

    # Resolve RxCUIs
    resolved = []
    for d in drugs_found[:2]:  # Take first two drugs found
        rxcui = drug_rxcui_map.get(d)
        if not rxcui:
            return None  # Cannot resolve -> return None (will become AMBIGUOUS)
        resolved.append((d, rxcui))

    predicate = normalize_predicate(predicates_found[0])

    # Direction: first drug mentioned is subject, second is object
    # This matches the "A affects B" convention from the annotation guide
    subject_name, subject_rxcui = resolved[0]
    object_name, object_rxcui = resolved[1]

    # Determine position in text for direction
    subj_pos = claim_text.lower().find(subject_name)
    obj_pos = claim_text.lower().find(object_name)

    if subj_pos < obj_pos:
        direction = CanonicalDirection.A_TO_B
    elif obj_pos < subj_pos:
        direction = CanonicalDirection.B_TO_A
        # Swap so subject is always the first in the canonical pair
        subject_rxcui, object_rxcui = object_rxcui, subject_rxcui
    else:
        direction = CanonicalDirection.UNKNOWN

    return CanonicalRelationshipIdentity(
        subject_rxcui=subject_rxcui,
        object_rxcui=object_rxcui,
        predicate=predicate,
        direction=direction,
    )
