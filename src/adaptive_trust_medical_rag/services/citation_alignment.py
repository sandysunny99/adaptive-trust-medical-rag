"""Whether a statement is attributed to the right one of the retrieved sources.

Citation alignment is separate from entailment. NLI answers "does this passage support the
statement?" and over-entails across sections of one drug label: the pinned PubMedBERT-MNLI-MedNLI
scored 0.998 for "Lisinopril can cause hyperkalemia in patients with renal insufficiency" against
lisinopril section 7.1 (diuretics), which mentions hyperkalemia but never renal insufficiency; the
fact is in section 5.5, which was also retrieved (round-4 eval example E25, 2026-10-26). A true fact
attributed to the wrong section was released.

The rule is a deterministic screen and only ever withholds. A statement's attribution is not verified
when the sources it cites lack some of its content words and one other retrieved source contains every
one of them: the other source accounts for the whole gap, so the statement's wording is there, just not
in what it cites. Word coverage is a signal, not proof that the other source supports the statement.
Uncited sources are only ever evidence against an attribution, never for a statement, so a
better-matching source is not substituted for the cited one. A content word found in no retrieved
source (a paraphrase, or content the evidence lacks) is left to the verifier and the strength checks.

What counts as a content word is fixed by word class, not tuned on evaluation data: function words
(articles, pronouns, prepositions, conjunctions), modals and negation, generic clinical relation verbs
(cause, increase, interact ...; the verifier and the identity check judge the relation), and generic
people, medication and quantity words are ignored. Words are compared after stripping one inflection.

shortcut: misattribution is detected only against what was retrieved; if the supporting section was
not retrieved, a wrong citation is left to the verifier. A correctly cited statement whose only words
missing from its source occur in another section is still withheld (fails safe): "... raising blood
potassium" cited to 5.5 lacks only "blood", which 7.1 has; a one-word misattribution ("... in diabetes"
cited to 7.1) looks the same to a word screen. A stricter rule (every content word must be in the
cited text) was measured on 2026-10-26 and also withholds paraphrases and structured field labels
("severity major"); removing either limit needs a reviewed synonym list or concept matching.
"""

from __future__ import annotations

import re

_MARKER_RE = re.compile(r"\[Source\s+\d+\]", re.IGNORECASE)
_WORD_RE = re.compile(r"[a-z][a-z-]{2,}")

_FUNCTION_WORDS = (
    # articles, determiners, pronouns
    "the this that these those its their there here who whom whose which what such "
    # prepositions
    "about above across after against along among around before behind below beside between beyond "
    "during except from into near onto over per since through throughout toward towards under until "
    "upon via with within without "
    # conjunctions and adverbial connectives
    "and but nor yet also then than when while whereas whether because although though unless once "
    # modals, auxiliaries, negation
    "can cannot could may might must shall should will would are was were been being has have had "
    "does did not "
)
_GENERIC_RELATION_VERBS = (
    "cause causes caused causing result results resulted resulting lead leads led leading "
    "increase increases increased increasing decrease decreases decreased decreasing "
    "reduce reduces reduced reducing raise raises raised raising lower lowers lowered lowering "
    "interact interacts interacted interacting associate associated association "
    "affect affects affected affecting occur occurs occurred occurring "
)
_GENERIC_WORDS = (
    # people, use, medication
    "patient patients people person persons individual individuals "
    "use used uses using take takes taking taken receive receives receiving received "
    "drug drugs medication medications medicine medicines agent agents product products "
    # quantity and degree
    "all any each every some both either other others more most less least many much "
    # generic risk and effect nouns
    "risk risks effect effects "
)
IGNORED = frozenset((_FUNCTION_WORDS + _GENERIC_RELATION_VERBS + _GENERIC_WORDS).split())


def _stem(word: str) -> str:
    """Strip one inflectional ending (plural, past, progressive), keeping a stem of at least 4 letters.

    Both sides get the same stem, so "monitored" matches "monitor" and "discontinued" matches
    "discontinuing"; "need" and "bleed" are too short to be cut.
    """
    for suffix in ("ies", "ing", "es", "ed", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)]
    return word


_HYPHENS = re.compile("[‐-–−]")  # the model writes U+2011 ("potassium‑sparing"); labels use "-"


def _words(text: str) -> list[str]:
    return _WORD_RE.findall(_HYPHENS.sub("-", text).lower())


def _stems(texts: list[str]) -> set[str]:
    return {_stem(w) for t in texts for w in _words(t)}


def content_terms(text: str) -> dict[str, str]:
    """The statement's content words (as written) mapped to their stems; ignored classes removed."""
    return {w: _stem(w) for w in _words(_MARKER_RE.sub(" ", text)) if w not in IGNORED}


def uncited_terms(statement: str, cited_texts: list[str]) -> list[str]:
    """The statement's content words (as written) that none of its cited texts contains, sorted."""
    present = _stems(cited_texts)
    return sorted(w for w, s in content_terms(statement).items() if s not in present)


def misattributed_terms(statement: str, cited_texts: list[str], other_texts: list[str]) -> list[str]:
    """The content words the cited texts lack, when one other retrieved text contains all of them.

    One other source must account for the whole gap: a single shared word is not enough (a correct
    paraphrase "raise blood potassium in kidney impairment" cited to the hyperkalemia section is not
    misattributed because "blood" occurs in the diuretics section's "blood pressure"). Empty when the
    cited texts lack nothing, or no single other source has every missing word.
    """
    missing = uncited_terms(statement, cited_texts)
    if missing and any({_stem(w) for w in missing} <= _stems([other]) for other in other_texts):
        return missing
    return []


def citation_alignment_violation(statement: str, cited_texts: list[str], other_texts: list[str]) -> str | None:
    """Why the statement is attributed to the wrong retrieved source, or None.

    ``cited_texts`` are the sources the statement cites; ``other_texts`` the other retrieved, eligible
    sources. No cited text at all is a violation: a statement must rest on the sources it names.
    """
    if not cited_texts:
        return "the statement cites no retrieved source"
    misplaced = misattributed_terms(statement, cited_texts, other_texts)
    if misplaced:
        # A word screen, not proof of which source supports the statement: it withholds, never re-attributes.
        return ("attribution not verified: the cited source does not mention, though another retrieved "
                "source does: " + ", ".join(misplaced))
    return None
