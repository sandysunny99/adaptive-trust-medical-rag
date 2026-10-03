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
    drugs_found = list(dict.fromkeys(m.lower() for m in _DRUG_PATTERN.findall(claim_text)))
    predicates_found = _PREDICATE_PATTERN.findall(claim_text)
    
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
