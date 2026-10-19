"""Whether an evidence chunk's recorded URL may be offered as a link to its original document.

The frozen live corpus records a URL for every chunk, but none of them was checked against the
document it names. Most DailyMed entries carry a placeholder set ID (``setid=example-...``), and
one PubMed ID is attached to two unrelated documents. A link that opens the wrong page would
misattribute the evidence, so a URL is offered as a link only when it is VERIFIED: listed for
that exact chunk in ``verified_links``, which only a researcher-approved source record may fill.
None is approved yet. Every other URL is still shown, as text, with the reason it is not a link.
"""

from __future__ import annotations

import re
from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any
from urllib.parse import urlsplit

VERIFIED = "VERIFIED"
PLACEHOLDER = "PLACEHOLDER"
SHARED = "SHARED"
UNVERIFIED = "UNVERIFIED"
MISSING = "MISSING"

NOTES = {
    VERIFIED: "Verified link to the original document.",
    PLACEHOLDER: "Placeholder link in the frozen corpus; it does not identify the original document.",
    SHARED: "The corpus attaches this link to more than one document, so it cannot identify this one.",
    UNVERIFIED: "This link has not been verified to open the original document.",
    MISSING: "No source link is recorded for this evidence.",
}

_PLACEHOLDER_RE = re.compile(
    r"[?&]setid=example-|^https?://(?:[\w-]+\.)*example\.(?:com|org|net|test)(?:[/:?#]|$)",
    re.IGNORECASE,
)


def normalise_url(url: str) -> str:
    """The URL without case differences in scheme and host or a trailing slash."""
    parts = urlsplit(url.strip())
    query = f"?{parts.query}" if parts.query else ""
    return f"{parts.scheme.lower()}://{parts.netloc.lower()}{parts.path.rstrip('/')}{query}"


def shared_urls(corpus_items: Iterable[Mapping[str, Any]]) -> frozenset[str]:
    """Normalised URLs that the corpus attaches to more than one document ID."""
    documents: dict[str, set[Any]] = defaultdict(set)
    for item in corpus_items:
        url = item.get("document_url")
        if url:
            documents[normalise_url(url)].add(item.get("document_id"))
    return frozenset(url for url, docs in documents.items() if len(docs) > 1)


def source_link(
    chunk_id: str,
    url: str | None,
    *,
    verified_links: Mapping[str, str] | None = None,
    shared: frozenset[str] = frozenset(),
) -> dict[str, str]:
    """The link status of one chunk's URL and the note shown with it."""
    if not url:
        status = MISSING
    elif (verified_links or {}).get(chunk_id) == url and url.lower().startswith("https://"):
        status = VERIFIED
    elif _PLACEHOLDER_RE.search(url):
        status = PLACEHOLDER
    elif normalise_url(url) in shared:
        status = SHARED
    else:
        status = UNVERIFIED
    return {"status": status, "note": NOTES[status]}
