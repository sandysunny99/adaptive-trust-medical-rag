"""Build the REL-LIVE-0004 candidate (warfarin with ibuprofen, bleeding risk) from DailyMed.

Source: warfarin sodium tablets SPL by set ID, section 7.3 "Drugs that Increase Bleeding Risk", verbatim
(XML text, whitespace collapsed). It names both drugs and advises close monitoring. The ibuprofen label's
"Warfarin-type anticoagulants" section also describes the risk, but its XML runs words together
("Ibuprofentablets"), so it never names ibuprofen as a whole word and cannot be a record source.

Writes reports/live_validation/runs/2026-10-22-audit/rel_live_0004_candidate/ (V2 format), status
CANDIDATE_PENDING_RESEARCHER_APPROVAL, severity UNGRADED (rejected by the loader until graded). Separate
from REL-LIVE-0003 and FOOD-0001; once approved it goes in its own relationships/v2/rel_live_0004/ folder.

    uv run python scripts/build_rel_live_0004_candidate.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_rel_live_0003_candidate import DAILYMED, NS, sha, text_of  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "live_validation" / "runs" / "2026-10-22-audit" / "rel_live_0004_candidate"
SETID = "884cdbf6-0a52-4126-8e14-b0d7c9367e33"  # WARFARIN SODIUM tablets
LABEL_URL = f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={SETID}"
SECTION_TITLE = "7.3 Drugs that Increase Bleeding Risk"
RXCUIS = {"warfarin": "11289", "ibuprofen": "5640"}
CHUNK_ID = "DAILYMED-884CDBF6-SPL-V8-SEC-7.3"
SUPPORTED_CLAIM = ("Ibuprofen is listed among drugs that can increase the risk of bleeding when used with warfarin, "
                   "and the label advises closely monitoring patients who receive it with warfarin.")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    captured_at = datetime.now(UTC).isoformat()
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        xml = client.get(f"{DAILYMED}/{SETID}.xml").raise_for_status().content
        history = client.get(f"{DAILYMED}/{SETID}/history.json").raise_for_status().json()
        rxnav = {n: client.get(f"https://rxnav.nlm.nih.gov/REST/rxcui/{c}/properties.json").raise_for_status()
                 .json()["properties"] for n, c in RXCUIS.items()}
    for name, props in rxnav.items():
        if props.get("name", "").lower() != name or props.get("suppress") != "N":
            raise SystemExit(f"RxCUI {RXCUIS[name]} does not resolve to an active {name}")

    root = etree.fromstring(xml)
    title = text_of(root.find("v3:title", NS))
    version = root.find("v3:versionNumber", NS).get("value")
    if "WARFARIN SODIUM" not in title.upper():
        raise SystemExit("label title does not name WARFARIN SODIUM")
    if str(history["data"]["history"][0]["spl_version"]) != version:
        raise SystemExit("captured SPL version is not the latest")
    sections = [s for s in root.iter("{urn:hl7-org:v3}section")
                if s.find("v3:title", NS) is not None and text_of(s.find("v3:title", NS)) == SECTION_TITLE]
    if len(sections) != 1:
        raise SystemExit(f"expected one section titled {SECTION_TITLE!r}, found {len(sections)}")
    text = text_of(sections[0])
    for name in RXCUIS:
        if f" {name}" not in f" {text.lower()}":
            raise SystemExit(f"section does not name {name}")

    from sentence_transformers import SentenceTransformer
    embedding = [float(x) for x in SentenceTransformer("all-MiniLM-L6-v2").encode([text])[0]]
    content_hash = sha(text.encode("utf-8"))
    document_id = f"DAILYMED-SPL-{SETID}"
    evidence = [{
        "chunk_id": CHUNK_ID, "document_id": document_id,
        "document_title": f"WARFARIN SODIUM tablets, SPL version {version}, section {SECTION_TITLE}",
        "document_url": LABEL_URL, "source_type": "DAILYMED", "text": text, "content_hash": content_hash,
        "authority": 0.95, "freshness": 0.9, "retrieved_at": captured_at, "embedding": embedding,
        "supported_claims": [{"text": SUPPORTED_CLAIM, "action": "MONITOR"}],
        "provenance": {"source": "DAILYMED", "document_id": document_id, "chunk_id": CHUNK_ID,
                       "content_hash": content_hash, "timestamp": captured_at},
        "source_identity": {
            "provider": "DAILYMED", "external_id": SETID, "canonical_url": LABEL_URL, "title": title,
            "section": SECTION_TITLE, "source_version": version,
            "published_date": history["data"]["history"][0].get("published_date"), "captured_at": captured_at,
            "capture_url": f"{DAILYMED}/{SETID}.xml", "capture_sha256": sha(xml),
            "verification_method": ("SPL XML downloaded from the DailyMed v2 API by set ID; title names the drug; "
                                    "version equals the latest in the SPL history; section text is the XML text "
                                    "of that section with whitespace collapsed."),
        },
    }]
    records = {"dataset_version": "LIVE_RELATIONSHIP_RECORDS_V2", "corpus_version": "LIVE_MEDICAL_CORPUS_V2",
               "records": [{
                   "record_id": "REL-LIVE-0004",
                   "subject": {"name": "warfarin", "rxcui": RXCUIS["warfarin"]},
                   "object": {"name": "ibuprofen", "rxcui": RXCUIS["ibuprofen"]},
                   "predicate": "INTERACTION", "direction": "BIDIRECTIONAL",
                   # The label gives no grade; UNGRADED is rejected by the loader until a researcher grades it.
                   "severity": "UNGRADED",
                   "source_chunk_id": CHUNK_ID, "source_content_hash": content_hash, "evidence_span": text,
               }]}
    evidence_raw = (json.dumps(evidence, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    records_raw = (json.dumps(records, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    (OUT / "LIVE_RELATIONSHIP_EVIDENCE_V2.json").write_bytes(evidence_raw)
    (OUT / "LIVE_RELATIONSHIP_RECORDS_V2.json").write_bytes(records_raw)
    lf = lambda b: hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()  # noqa: E731
    manifest = {
        "dataset_version": "LIVE_RELATIONSHIP_RECORDS_V2", "candidate_id": "REL-LIVE-0004",
        "records_file": "LIVE_RELATIONSHIP_RECORDS_V2.json", "records_sha256": lf(records_raw),
        "evidence_file": "LIVE_RELATIONSHIP_EVIDENCE_V2.json", "evidence_sha256": lf(evidence_raw),
        "corpus_version": "LIVE_MEDICAL_CORPUS_V2",
        "status": "CANDIDATE_PENDING_RESEARCHER_APPROVAL", "approval": None,
        "supported_claim": SUPPORTED_CLAIM,
        "not_supported": ["any severity grade", "a numerical risk", "avoiding the combination",
                          "stopping or changing either medicine"],
        "source_capture": {"spl_setid": SETID, "spl_version": version, "spl_sha256": sha(xml),
                           "rxnav": {n: {"rxcui": RXCUIS[n], "name": p.get("name"), "tty": p.get("tty")}
                                     for n, p in rxnav.items()}, "captured_at": captured_at},
        "prepared": {"by": "Claude (AI-prepared candidate; not a reviewer)", "on": captured_at[:10],
                     "script": "scripts/build_rel_live_0004_candidate.py"},
        "verification_required_before_approval": [
            f"Open {LABEL_URL} and confirm section {SECTION_TITLE} reads as the evidence text.",
            "Grade the severity with the project's documented method (it is UNGRADED, so the loader rejects it).",
            "Confirm the reviewed wording (MONITOR) and predicate INTERACTION, direction BIDIRECTIONAL.",
        ],
        "how_to_approve": ("Grade the severity and recompute records_sha256 for the edited records file, then copy "
                           "the three files into data/live_medical/relationships/v2/rel_live_0004/ (each approved V2 "
                           "dataset has its own folder; never copy over another dataset's files), and set status to "
                           "APPROVED and approval to {\"approved_by\": \"<name>\", \"approved_at\": \"<YYYY-MM-DD>\"}."),
    }
    (OUT / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"chunk_id": CHUNK_ID, "content_hash": content_hash, "spl_version": version,
                      "chars": len(text)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
