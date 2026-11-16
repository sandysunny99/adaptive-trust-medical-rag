"""Build the REL-LIVE-0003 candidate (lisinopril with spironolactone, hyperkalemia) from DailyMed.

It downloads, byte for byte, the lisinopril prescribing information (SPL XML) by set ID, its
version history and the RxNav properties of both RxCUIs; it checks that the label is the one
named (title and version), takes section 7.1 "Diuretics" verbatim (XML text with whitespace
collapsed to single spaces, nothing else changed), and writes a V2 relationship dataset:

    reports/live_validation/runs/2026-10-22-audit/rel_live_0003_candidate/
        LIVE_RELATIONSHIP_EVIDENCE_V2.json, LIVE_RELATIONSHIP_RECORDS_V2.json,
        LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json  (CANDIDATE), and the raw captures

The manifest is CANDIDATE_PENDING_RESEARCHER_APPROVAL, so the application loads nothing until a
named researcher checks the record against the label and approves it. Raw downloads go to
source_capture/ (git-ignored). The frozen corpus is not touched. Free public endpoints only.

    uv run python scripts/build_rel_live_0003_candidate.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
# The candidate is written beside its audit run, never into data/live_medical/relationships, so the
# live application cannot load it; approval means copying it there with an APPROVED manifest.
REL_DIR = ROOT / "reports" / "live_validation" / "runs" / "2026-10-22-audit" / "rel_live_0003_candidate"
CAPTURE_DIR = REL_DIR

SETID = "34ebeea1-6812-4697-84c4-b2ae4f39e55f"   # LISINOPRIL tablet, Bluepoint Laboratories
EXPECTED_TITLE_DRUG = "LISINOPRIL TABLETS"
SECTION_TITLE = "7.1 Diuretics"
RXCUIS = {"lisinopril": "29046", "spironolactone": "9997"}
CHUNK_ID = "DAILYMED-34EBEEA1-SPL-V12-SEC-7.1"
DAILYMED = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls"
LABEL_URL = f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={SETID}"
NS = {"v3": "urn:hl7-org:v3"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# SPL narrative elements that end a run of text. Inline markup (<content>, <sub>, <sup>, links)
# joins its text as written; words run together inside one text node are left as published.
BLOCK_TAGS = {"section", "title", "text", "paragraph", "list", "item", "table", "caption",
              "thead", "tbody", "tfoot", "tr", "td", "th", "br"}


def text_of(node) -> str:
    """The text of an SPL node with whitespace collapsed to single spaces ("" for None)."""
    if node is None:
        return ""
    parts: list[str] = []

    def walk(el) -> None:
        block = isinstance(el.tag, str) and etree.QName(el).localname in BLOCK_TAGS
        if block:
            parts.append(" ")
        if isinstance(el.tag, str) and el.text:  # comments and processing instructions add nothing
            parts.append(el.text)
        for child in el:
            walk(child)
            if child.tail:
                parts.append(child.tail)
        if block:
            parts.append(" ")

    walk(node)
    return " ".join("".join(parts).split())


def fetch(client: httpx.Client, url: str, name: str) -> bytes:
    resp = client.get(url)
    resp.raise_for_status()
    if not resp.content:
        raise ValueError(f"{url}: empty response")
    (CAPTURE_DIR / name).write_bytes(resp.content)
    return resp.content


def main() -> int:
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    captured_at = datetime.now(UTC).isoformat()
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        xml = fetch(client, f"{DAILYMED}/{SETID}.xml", f"spl_{SETID}.xml")
        history = json.loads(fetch(client, f"{DAILYMED}/{SETID}/history.json", f"spl_{SETID}_history.json"))
        rxnav = {name: json.loads(fetch(client, f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json",
                                        f"rxnav_{rxcui}_properties.json"))["properties"]
                 for name, rxcui in RXCUIS.items()}

    for name, props in rxnav.items():
        if props.get("name", "").lower() != name or props.get("suppress") != "N":
            raise SystemExit(f"RxCUI {RXCUIS[name]} does not resolve to an active {name}: {props}")

    root = etree.fromstring(xml)
    title = text_of(root.find("v3:title", NS))
    version = root.find("v3:versionNumber", NS).get("value")
    effective = root.find("v3:effectiveTime", NS).get("value")
    if EXPECTED_TITLE_DRUG not in title.upper():
        raise SystemExit(f"label title does not name {EXPECTED_TITLE_DRUG}: {title[:120]}")
    latest = history["data"]["history"][0]
    if str(latest["spl_version"]) != version:
        raise SystemExit(f"captured SPL version {version} is not the latest ({latest['spl_version']})")

    sections = [s for s in root.iter("{urn:hl7-org:v3}section")
                if s.find("v3:title", NS) is not None and text_of(s.find("v3:title", NS)) == SECTION_TITLE]
    if len(sections) != 1:
        raise SystemExit(f"expected one section titled {SECTION_TITLE!r}, found {len(sections)}")
    text = text_of(sections[0])
    for name in RXCUIS:
        if name not in text.lower():
            raise SystemExit(f"section {SECTION_TITLE} does not name {name}")

    from sentence_transformers import SentenceTransformer
    embedding = [float(x) for x in SentenceTransformer("all-MiniLM-L6-v2").encode([text])[0]]

    content_hash = sha(text.encode("utf-8"))
    evidence = [{
        "chunk_id": CHUNK_ID,
        "document_id": f"DAILYMED-SPL-{SETID}",
        "document_title": f"LISINOPRIL tablet (Bluepoint Laboratories), SPL version {version}, section {SECTION_TITLE}",
        "document_url": LABEL_URL,
        "source_type": "DAILYMED",
        "text": text,
        "content_hash": content_hash,
        "authority": 0.95,
        "freshness": 0.9,
        "retrieved_at": captured_at,
        "embedding": embedding,
        "provenance": {"source": "DAILYMED", "document_id": f"DAILYMED-SPL-{SETID}", "chunk_id": CHUNK_ID,
                       "content_hash": content_hash, "timestamp": captured_at},
        "source_identity": {
            "provider": "DAILYMED",
            "external_id": SETID,
            "canonical_url": LABEL_URL,
            "title": title,
            "section": SECTION_TITLE,
            "source_version": version,
            "effective_time": effective,
            "published_date": latest.get("published_date"),
            "captured_at": captured_at,
            "capture_url": f"{DAILYMED}/{SETID}.xml",
            "capture_sha256": sha(xml),
            "verification_method": ("SPL XML downloaded from the DailyMed v2 API by set ID; title names the drug; "
                                    "version equals the latest in the SPL history; section text is the XML text "
                                    "of that section with whitespace collapsed."),
        },
    }]
    records = {
        "dataset_version": "LIVE_RELATIONSHIP_RECORDS_V2",
        "corpus_version": "LIVE_MEDICAL_CORPUS_V2",
        "records": [{
            "record_id": "REL-LIVE-0003",
            "subject": {"name": "lisinopril", "rxcui": RXCUIS["lisinopril"]},
            "object": {"name": "spironolactone", "rxcui": RXCUIS["spironolactone"]},
            "predicate": "INTERACTION",
            "direction": "BIDIRECTIONAL",
            # The label gives no severity grade, so none is assigned. UNGRADED is not a loadable
            # severity: the record is rejected until a researcher grades it by the documented method.
            "severity": "UNGRADED",
            "source_chunk_id": CHUNK_ID,
            "source_content_hash": content_hash,
            "evidence_span": text,
        }],
    }

    REL_DIR.mkdir(parents=True, exist_ok=True)
    evidence_raw = (json.dumps(evidence, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    records_raw = (json.dumps(records, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    (REL_DIR / "LIVE_RELATIONSHIP_EVIDENCE_V2.json").write_bytes(evidence_raw)
    (REL_DIR / "LIVE_RELATIONSHIP_RECORDS_V2.json").write_bytes(records_raw)
    manifest = {
        "dataset_version": "LIVE_RELATIONSHIP_RECORDS_V2",
        "records_file": "LIVE_RELATIONSHIP_RECORDS_V2.json",
        "records_sha256": sha(records_raw.replace(b"\r\n", b"\n")),
        "evidence_file": "LIVE_RELATIONSHIP_EVIDENCE_V2.json",
        "evidence_sha256": sha(evidence_raw.replace(b"\r\n", b"\n")),
        "hash_note": "SHA-256 of each file with CRLF normalised to LF, so Windows and Linux checkouts agree.",
        "corpus_version": "LIVE_MEDICAL_CORPUS_V2",
        "status": "CANDIDATE_PENDING_RESEARCHER_APPROVAL",
        "approval": None,
        "prepared": {
            "by": "Claude (AI-prepared candidate; not a reviewer)",
            "on": captured_at[:10],
            "script": "scripts/build_rel_live_0003_candidate.py",
        },
        "source_capture": {
            "spl_setid": SETID, "spl_version": version, "spl_title": title,
            "spl_sha256": sha(xml), "rxnav": {n: {"rxcui": RXCUIS[n], "name": p.get("name"), "tty": p.get("tty"),
                                                   "suppress": p.get("suppress")} for n, p in rxnav.items()},
            "captured_at": captured_at,
        },
        "verification_required_before_approval": [
            f"Open {LABEL_URL} and confirm section {SECTION_TITLE} reads as the evidence_span "
            "(it names spironolactone among potassium-sparing diuretics that can increase the risk of hyperkalemia).",
            ("Grade the severity with the project's documented severity method and set it to one of "
             "CONTRAINDICATED, MAJOR, MODERATE, MINOR or NONE. It is UNGRADED: the label gives no grade, and an "
             "UNGRADED record is rejected by the loader even if the manifest is approved. Confirm predicate "
             "INTERACTION and direction BIDIRECTIONAL."),
            "Confirm RxCUIs 29046 (lisinopril) and 9997 (spironolactone) with RxNav.",
        ],
        "how_to_approve": ("Grade the severity and recompute records_sha256 for the edited records file, then copy "
                           "the three files into data/live_medical/relationships/v2/rel_live_0003/ (each approved V2 "
                           "dataset has its own folder; never copy over another dataset's files), and set status to "
                           "APPROVED and approval to {\"approved_by\": \"<name>\", \"approved_at\": \"<YYYY-MM-DD>\"}."),
        "use_in_application": ("None until APPROVED. Once approved the chunk joins retrieval, is identity-verified "
                               "through its source_identity record, raises the pair to R3, and gives claims "
                               "about this pair a relationship identity for verification."),
    }
    (REL_DIR / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"chunk_id": CHUNK_ID, "content_hash": content_hash, "spl_version": version,
                      "title": title[:100], "text_chars": len(text)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
