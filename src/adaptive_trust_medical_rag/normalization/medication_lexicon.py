"""Offline medication-name recognition from a pinned RxNorm Current Prescribable Content lexicon.

The lexicon (data/terminology/rxnorm_prescribable_<release>/, built by scripts/build_rxnorm_prescribable_lexicon.py)
lists active RxNorm ingredients (IN), precise ingredients such as salts (PIN), multi-ingredient concepts (MIN) and
brand names (BN), each with its RxCUI. It is loaded once per process and only after its SHA-256 matches the
manifest; a missing, altered or unreadable artifact raises LexiconUnavailable, and callers fail closed.

Matching is deterministic and whole-token: text and names are cut into alphanumeric tokens (Unicode hyphens and
punctuation separate tokens), and at each position the longest name wins, so "metoprolol succinate" (PIN) is not
read as "metoprolol" (IN). Ingredient names match in any case; brand names only as RxNorm writes them ("Lasix"),
because many brands are ordinary words ("React", "Perform"). A name needs a token of three or more letters ("S-2"
is skipped). Two different concepts on the same span are reported as ambiguous, never guessed.

shortcut: recognition covers only this subset's names (US prescribable and many OTC drugs, active only); a foreign,
withdrawn or invented name is not seen. Synonyms beyond RxNorm's normalised names are not included.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

LEXICON_DIR = Path(__file__).resolve().parents[3] / "data" / "terminology" / "rxnorm_prescribable_2026-10-05"
FORMAT = "rxnorm-prescribable-lexicon/1"
TTYS = frozenset({"IN", "PIN", "MIN", "BN"})
_TOKEN_RE = re.compile(r"[^\W_]+")
_LETTERS_RE = re.compile(r"[^\W\d_]{3,}")


class LexiconUnavailable(RuntimeError):
    """The medication lexicon is missing, altered or unreadable; medication identity cannot be checked."""


@dataclass(frozen=True)
class Mention:
    text: str  # as written in the statement
    rxcui: str | None
    name: str | None  # the RxNorm name, None when ambiguous
    tty: str | None
    candidates: tuple[tuple[str, str, str], ...] = ()  # (rxcui, name, tty) for every concept on this span

    @property
    def ambiguous(self) -> bool:
        return len(self.candidates) > 1


class MedicationLexicon:
    def __init__(self, entries: list[dict], release: str = "test"):
        self.release = release
        self.size = len(entries)
        self._exact: dict[tuple[str, ...], set[tuple[str, str, str]]] = {}  # brand names, case kept
        self._folded: dict[tuple[str, ...], set[tuple[str, str, str]]] = {}  # every other term type
        for e in entries:
            if e["tty"] not in TTYS:
                raise LexiconUnavailable(f"unsupported term type {e['tty']!r}")
            tokens = tuple(_TOKEN_RE.findall(e["name"]))
            if not any(_LETTERS_RE.search(t) for t in tokens):
                continue
            index, key = (self._exact, tokens) if e["tty"] == "BN" else (self._folded, tuple(t.lower() for t in tokens))
            index.setdefault(key, set()).add((e["rxcui"], e["name"], e["tty"]))
        # The name lengths (in tokens) that start with each first token, longest first: one name runs to 231
        # tokens, so trying every length at every position would be slow.
        lengths: dict[str, set[int]] = {}
        for key in (*self._exact, *self._folded):
            lengths.setdefault(key[0].lower(), set()).add(len(key))
        self._lengths = {first: sorted(ns, reverse=True) for first, ns in lengths.items()}

    def mentions(self, text: str) -> list[Mention]:
        """Every lexicon name in the text, longest match first, left to right."""
        spans = [(m.start(), m.end(), m.group()) for m in _TOKEN_RE.finditer(text)]
        words = [w for _, _, w in spans]
        folded = [w.lower() for w in words]
        found, i = [], 0
        while i < len(words):
            for n in (n for n in self._lengths.get(folded[i], ()) if i + n <= len(words)):
                hits = self._exact.get(tuple(words[i:i + n]), set()) | self._folded.get(tuple(folded[i:i + n]), set())
                if hits:
                    ordered = tuple(sorted(hits))
                    rxcui, name, tty = ordered[0] if len(ordered) == 1 else (None, None, None)
                    found.append(Mention(text[spans[i][0]:spans[i + n - 1][1]], rxcui, name, tty, ordered))
                    i += n
                    break
            else:
                i += 1
        return found


def load_lexicon(folder: Path = LEXICON_DIR) -> MedicationLexicon:
    """The lexicon in ``folder``, after checking its bytes against the manifest's SHA-256."""
    try:
        manifest = json.loads((folder / "MANIFEST.json").read_text(encoding="utf-8"))
        raw = (folder / manifest["lexicon"]).read_bytes()
    except (OSError, ValueError, KeyError) as e:
        raise LexiconUnavailable(f"cannot read the medication lexicon in {folder.name}: {type(e).__name__}") from e
    if hashlib.sha256(raw).hexdigest() != manifest.get("lexicon_sha256"):
        raise LexiconUnavailable(f"the medication lexicon in {folder.name} does not match its recorded SHA-256")
    try:
        data = json.loads(raw)
        if data.get("format") != FORMAT or data.get("release") != manifest.get("release"):
            raise LexiconUnavailable(f"unsupported medication lexicon format or release in {folder.name}")
        return MedicationLexicon(data["entries"], data["release"])
    except (ValueError, KeyError, TypeError) as e:
        raise LexiconUnavailable(f"the medication lexicon in {folder.name} is malformed: {type(e).__name__}") from e


@lru_cache(maxsize=1)
def default_lexicon() -> MedicationLexicon:
    """The pinned lexicon, loaded and verified once per process (a failure is not cached)."""
    return load_lexicon()
