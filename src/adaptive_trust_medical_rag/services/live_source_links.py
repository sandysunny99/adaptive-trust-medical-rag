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


# ── Source identity ───────────────────────────────────────────────────────────────────────
# Whether a chunk is known to come from the external document it names. It is a hard gate,
# separate from every score: only an identity-VERIFIED chunk may be used as evidence, whatever
# its authority, freshness or retrieval score.
IDENTITY_VERIFIED = "VERIFIED"
IDENTITY_UNVERIFIED = "UNVERIFIED"
IDENTITY_REJECTED = "REJECTED_SOURCE_IDENTITY"

IDENTITY_NOTES = {
    IDENTITY_VERIFIED: "Source identity verified against the original document.",
    IDENTITY_UNVERIFIED: "Source identity not verified, so this text cannot be used as evidence.",
    IDENTITY_REJECTED: "Source identity rejected: the recorded link cannot identify the original document.",
}

# Fields a source identity record must carry (V2 evidence, captured from the original document).
IDENTITY_FIELDS = ("provider", "external_id", "canonical_url", "title", "source_version",
                   "captured_at", "capture_sha256", "verification_method")
_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def source_identity_status(link_status: str) -> str:
    """The identity status implied by a chunk's link status."""
    if link_status == VERIFIED:
        return IDENTITY_VERIFIED
    if link_status in (PLACEHOLDER, SHARED):
        return IDENTITY_REJECTED
    return IDENTITY_UNVERIFIED


def check_source_identity(item: Mapping[str, Any], shared: frozenset[str] = frozenset()) -> str:
    """'verified', or why an evidence item's source identity record does not identify its document.

    The record must be complete, name the same https URL as the item, and its external ID must be
    the one that URL resolves (a DailyMed set ID, a PubMed ID). A placeholder or a URL shared by
    several documents never verifies, whatever the record says.
    """
    ident = item.get("source_identity")
    if not isinstance(ident, Mapping):
        return "no source identity record"
    missing = [k for k in IDENTITY_FIELDS if not ident.get(k)]
    if missing:
        return f"source identity record is missing {', '.join(missing)}"
    url = str(item.get("document_url") or "")
    if ident["canonical_url"] != url:
        return "source identity canonical_url differs from the evidence document_url"
    if not url.lower().startswith("https://"):
        return "source URL is not https"
    if _PLACEHOLDER_RE.search(url):
        return "source URL is a placeholder"
    if normalise_url(url) in shared:
        return "source URL is attached to more than one document"
    if not _SHA256_RE.match(str(ident["capture_sha256"])):
        return "capture_sha256 is not a SHA-256 digest"
    provider = str(ident["provider"]).upper()
    external_id = str(ident["external_id"])
    parts = urlsplit(url)
    if provider == "DAILYMED":
        if not _UUID_RE.match(external_id):
            return "DailyMed external_id is not a set ID"
        if parts.netloc.lower() != "dailymed.nlm.nih.gov" or f"setid={external_id.lower()}" not in parts.query.lower():
            return "DailyMed URL does not resolve the recorded set ID"
    elif provider == "PUBMED":
        if not external_id.isdigit():
            return "PubMed external_id is not a PMID"
        if normalise_url(url) != f"https://pubmed.ncbi.nlm.nih.gov/{external_id}":
            return "PubMed URL does not resolve the recorded PMID"
    else:
        return f"source identity provider {provider} has no identity check"
    if str(item.get("source_type", "")).upper() != provider:
        return "source identity provider differs from the evidence source_type"
    return "verified"


def verified_links_from(items: Iterable[Mapping[str, Any]], shared: frozenset[str] = frozenset()) -> dict[str, str]:
    """chunk_id -> URL for every item whose source identity record verifies."""
    return {item["chunk_id"]: item["document_url"] for item in items
            if item.get("chunk_id") and check_source_identity(item, shared) == "verified"}
