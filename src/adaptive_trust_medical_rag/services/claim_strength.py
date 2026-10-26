"""Whether a generated statement claims more than its source's reviewed wording allows.

NLI answers "does the passage support this?" and can accept "avoid salt substitutes" against a passage
that only lists them as a risk factor (entailment 0.985 on 2026-10-22). This check is separate: each
approved evidence chunk may carry reviewed ``supported_claims`` ({"text", "action"}), and a statement
citing it may not exceed the strongest reviewed action, nor add certainty, a quantity, timing, a
duration, a patient population or an outcome severity that no reviewed claim states.

The cue lists catch overstatement; they are not the only guard. Food statements are released with the
reviewed wording, not the generated wording (see ``reviewed_food_lines``), so a paraphrase the lists
miss still never reaches the user. A food statement whose source has no reviewed wording fails closed.
"""

from __future__ import annotations

import re
from typing import Any

# Action ladder: a statement may claim up to the strongest action its source's reviewed wording has.
ACTION_LEVELS = {
    "RISK_ASSOCIATION": 1, "MONITOR": 1,
    "CAUTION": 2, "DISCUSS_WITH_CLINICIAN": 2, "KEEP_CONSISTENT": 2,
    "LIMIT": 3, "AVOID": 4, "CHANGE_MEDICATION": 5, "PERSONAL_PLAN": 5,
}

_CUES: tuple[tuple[str, re.Pattern[str]], ...] = tuple((action, re.compile(pattern, re.IGNORECASE)) for action, pattern in (
    ("CHANGE_MEDICATION", r"\b(stop|discontinue|switch|hold|skip)\b[^.;]{0,30}\b(medicine|medication|drug|dose|tablet|lisinopril|treatment)|"
                          r"\b(reduce|lower|increase|change|adjust)\b[^.;]{0,15}\bdose\b"),
    ("PERSONAL_PLAN", r"\b(diet|meal|treatment|eating|nutrition)\s+plan\b"),
    ("AVOID", r"\b(avoid|avoided|avoiding|never|eliminate|refrain|abstain|prohibit\w*|forbid\w*|contraindicat\w*|"
              r"steer clear|stay away|cut out|keep away|must not|should not|shouldn't|do not|don't|"
              r"not (?:be )?(?:use|used|take|taken|consume|consumed|eat|eaten|allowed)|skip)\b"),
    ("LIMIT", r"\b(limit\w*|restrict\w*|reduce|reducing|cut (?:back|down)|minimi[sz]e|moderat\w*|less|fewer|"
              r"no more than|at most|maximum|up to|below|lower than)\b"),
    ("KEEP_CONSISTENT", r"\b(consistent|consistently|same amount|steady)\b"),
    ("CAUTION", r"\b(caution|careful|carefully|be aware)\b"),
    ("DISCUSS_WITH_CLINICIAN", r"\b(talk to|ask (?:your|a)|discuss|consult|check with)\b"),
))
# Claims a source must state outright, beyond its action.
_EXTRAS: tuple[tuple[str, re.Pattern[str]], ...] = tuple((name, re.compile(pattern, re.IGNORECASE)) for name, pattern in (
    ("CERTAINTY", r"\b(will|always|definitely|certainly|guarantee\w*|must|in all (?:cases|patients))\b"),
    ("QUANTITY", r"\b\d+(?:\.\d+)?\s*(?:mg|g|grams?|mmol|meq|mEq|servings?|cups?|teaspoons?|tsp|percent|%)\b|"
                 r"\b(per day|a day|daily|each day|per week)\b"),
    ("TIMING", r"\b(empty stomach|with food|without food|before (?:meals|food|eating)|after (?:meals|food|eating)|"
               r"at bedtime|hours? (?:before|after|apart)|immediately|at once|right away|hourly|weekly|monthly)\b"),
    # Round 5: with an over-entailing NLI these were released when no source stated them. A population is its
    # own class, so a source about pregnancy never vouches for children. Outcome severity only: the answer
    # schema's grades ("common | important | serious") are field labels, not outcome claims.
    ("DURATION", r"\b\d+(?:\.\d+)?\s*(?:(?:to|-)\s*\d+(?:\.\d+)?\s*)?(?:minutes?|hours?|hrs?|days?|weeks?|months?|years?)\b"),
    ("PEDIATRIC", r"\b(pediatric|paediatric|child|children|infants?|neonat\w*|newborns?|adolescents?)\b"),
    ("GERIATRIC", r"\b(geriatric|elderly|older (?:adults?|patients|people))\b"),
    ("PREGNANCY", r"\b(pregnan\w*|fetal|fetus|foetal|foetus)\b"),
    ("LACTATION", r"\b(lactat\w*|breast[- ]?feed\w*|breastfed|nursing (?:mothers?|women|infants?))\b"),
    ("SEVERITY", r"\b(fatal\w*|lethal|deadly|life[- ]threatening|death|deaths|die|dies|died)\b"),
))


def claimed_strength(text: str) -> tuple[int, list[str], list[str]]:
    """The strongest action level the text claims, the actions found, and any extra claims."""
    actions = [action for action, pattern in _CUES if pattern.search(text)]
    extras = [name for name, pattern in _EXTRAS if pattern.search(text)]
    level = max((ACTION_LEVELS[a] for a in actions), default=ACTION_LEVELS["RISK_ASSOCIATION"])
    return level, actions, extras


def reviewed_claims(chunk_metadata: dict[str, Any]) -> list[dict[str, Any]]:
    claims = chunk_metadata.get("supported_claims") or []
    return [c for c in claims if isinstance(c, dict) and c.get("text") and c.get("action") in ACTION_LEVELS]


def strength_violation(text: str, cited_metadata: list[dict[str, Any]]) -> str | None:
    """Why the statement claims more than its sources' reviewed wording allows, or None.

    Only sources with reviewed wording constrain the statement; a statement citing none is not judged
    here. The extras (certainty, quantity, timing) must appear in a reviewed claim's ``allows`` list.
    """
    claims = [c for meta in cited_metadata for c in reviewed_claims(meta)]
    if not claims:
        return None
    allowed = max(ACTION_LEVELS[c["action"]] for c in claims)
    allowed_extras = {e for c in claims for e in c.get("allows", [])}
    level, actions, extras = claimed_strength(text)
    if level > allowed:
        strongest = max(actions, key=lambda a: ACTION_LEVELS[a])
        return f"claims {strongest} but the source's reviewed wording supports at most level {allowed}"
    unsupported = [e for e in extras if e not in allowed_extras]
    if unsupported:
        return f"adds {', '.join(unsupported)} that the source's reviewed wording does not state"
    return None


def reviewed_food_lines(cited: dict[int, dict[str, Any]]) -> list[str]:
    """The reviewed wording of each cited source, with its [Source N] marker; what is released."""
    return [f"{c['text']} [Source {n}]" for n, meta in sorted(cited.items()) for c in reviewed_claims(meta)]


_MARKER_RE = re.compile(r"\[Source\s+\d+\]", re.IGNORECASE)


def source_text_violation(text: str, source_texts: list[str]) -> str | None:
    """Why the statement claims more than its cited sources' own text, for sources with no reviewed
    wording; None when it does not.

    The same cue lists bound the statement by the cited text itself: it may not claim a stronger
    action than the text contains, nor certainty, a quantity or timing the text does not state. NLI
    alone accepted "Thiazide diuretics should be stopped in all patients taking lisinopril" against
    a label that only says the diuretic may be decreased or discontinued (2026-10-26). This only
    ever withholds.
    """
    if not source_texts:
        return None
    level, actions, extras = claimed_strength(_MARKER_RE.sub("", text))
    found = [claimed_strength(t) for t in source_texts]
    allowed = max(f[0] for f in found)
    allowed_extras = {e for f in found for e in f[2]}
    if level > allowed:
        strongest = max(actions, key=lambda a: ACTION_LEVELS[a])
        return f"claims {strongest}, stronger than the cited text states"
    unsupported = [e for e in extras if e not in allowed_extras]
    if unsupported:
        return f"adds {', '.join(unsupported)} that the cited text does not state"
    return None
