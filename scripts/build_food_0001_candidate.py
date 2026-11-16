"""Build the FOOD-0001 candidate: lisinopril label section 5.5 (potassium-containing salt substitutes).

Single-drug food evidence has no drug pair, so it is a standalone V2 evidence chunk that the manifest
lists in ``standalone_evidence_chunks`` (no relationship record). It downloads the lisinopril SPL by
set ID, checks title and latest version, takes section 5.5 verbatim (whitespace collapsed) and writes:

    reports/live_validation/runs/2026-10-22-audit/food_0001_candidate/
        LIVE_RELATIONSHIP_EVIDENCE_V2.json, LIVE_RELATIONSHIP_RECORDS_V2.json (no records),
        LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json  (CANDIDATE_PENDING_RESEARCHER_APPROVAL)

Nothing loads until a named researcher approves it. It is separate from REL-LIVE-0003 and carries no
severity grade. Each approved V2 dataset has its own relationships/v2/<folder>/, so nothing is merged.

    uv run python scripts/build_food_0001_candidate.py
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
from build_rel_live_0003_candidate import (  # noqa: E402
    DAILYMED,
    EXPECTED_TITLE_DRUG,
    LABEL_URL,
    NS,
    SETID,
    sha,
    text_of,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "live_validation" / "runs" / "2026-10-22-audit" / "food_0001_candidate"
SECTION_TITLE = "5.5 Hyperkalemia"
CHUNK_ID = "DAILYMED-34EBEEA1-SPL-V12-SEC-5.5"
# The narrow statement the passage supports. It is a risk factor with monitoring, not an instruction
# to avoid: the reviewer must keep generated wording within this.
SUPPORTED_CLAIM = ("Potassium-containing salt substitutes are listed as a risk factor for hyperkalemia in "
                   "patients receiving lisinopril, and the label advises periodic serum potassium monitoring.")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    captured_at = datetime.now(UTC).isoformat()
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        xml = client.get(f"{DAILYMED}/{SETID}.xml").raise_for_status().content
        history = client.get(f"{DAILYMED}/{SETID}/history.json").raise_for_status().json()

    root = etree.fromstring(xml)
    title = text_of(root.find("v3:title", NS))
    version = root.find("v3:versionNumber", NS).get("value")
    if EXPECTED_TITLE_DRUG not in title.upper():
        raise SystemExit(f"label title does not name {EXPECTED_TITLE_DRUG}")
    if str(history["data"]["history"][0]["spl_version"]) != version:
        raise SystemExit("captured SPL version is not the latest")
    sections = [s for s in root.iter("{urn:hl7-org:v3}section")
                if s.find("v3:title", NS) is not None and text_of(s.find("v3:title", NS)) == SECTION_TITLE]
    if len(sections) != 1:
        raise SystemExit(f"expected one section titled {SECTION_TITLE!r}, found {len(sections)}")
    text = text_of(sections[0])
    for needed in ("lisinopril", "potassium-containing salt substitutes"):
        if needed not in text.lower():
            raise SystemExit(f"section {SECTION_TITLE} does not mention {needed}")

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
        # The wording a statement citing this chunk may not exceed, and the only food wording released.
        # Prepared for researcher review; the manifest approval covers it.
        "supported_claims": [{"text": SUPPORTED_CLAIM, "action": "MONITOR"}],
        "provenance": {"source": "DAILYMED", "document_id": f"DAILYMED-SPL-{SETID}", "chunk_id": CHUNK_ID,
                       "content_hash": content_hash, "timestamp": captured_at},
        "source_identity": {
            "provider": "DAILYMED", "external_id": SETID, "canonical_url": LABEL_URL, "title": title,
            "section": SECTION_TITLE, "source_version": version,
            "published_date": history["data"]["history"][0].get("published_date"),
            "captured_at": captured_at, "capture_url": f"{DAILYMED}/{SETID}.xml", "capture_sha256": sha(xml),
            "verification_method": ("SPL XML downloaded from the DailyMed v2 API by set ID; title names the drug; "
                                    "version equals the latest in the SPL history; section text is the XML text "
                                    "of that section with whitespace collapsed."),
        },
    }]
    records = {"dataset_version": "LIVE_RELATIONSHIP_RECORDS_V2", "corpus_version": "LIVE_MEDICAL_CORPUS_V2",
               "records": []}
    evidence_raw = (json.dumps(evidence, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    records_raw = (json.dumps(records, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    (OUT / "LIVE_RELATIONSHIP_EVIDENCE_V2.json").write_bytes(evidence_raw)
    (OUT / "LIVE_RELATIONSHIP_RECORDS_V2.json").write_bytes(records_raw)
    lf = lambda b: hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()  # noqa: E731
    manifest = {
        "dataset_version": "LIVE_RELATIONSHIP_RECORDS_V2",
        "candidate_id": "FOOD-0001",
        "records_file": "LIVE_RELATIONSHIP_RECORDS_V2.json", "records_sha256": lf(records_raw),
        "evidence_file": "LIVE_RELATIONSHIP_EVIDENCE_V2.json", "evidence_sha256": lf(evidence_raw),
        "standalone_evidence_chunks": [CHUNK_ID],
        "corpus_version": "LIVE_MEDICAL_CORPUS_V2",
        "status": "CANDIDATE_PENDING_RESEARCHER_APPROVAL",
        "approval": None,
        "claim_category": "FOOD_DRUG_INTERACTION",
        "food_entity": "potassium-containing salt substitutes",
        "medication": {"name": "lisinopril", "rxcui": "29046"},
        "supported_claim": SUPPORTED_CLAIM,
        "patient_context_relevance": ("The passage also lists renal insufficiency and diabetes mellitus as "
                                      "hyperkalemia risk factors; it sets no potassium limit and no diet."),
        "not_supported": ["avoiding all potassium-containing foods", "any daily potassium limit or diet plan",
                          "any severity grade", "stopping or changing a medicine"],
        "prepared": {"by": "Claude (AI-prepared candidate; not a reviewer)", "on": captured_at[:10],
                     "script": "scripts/build_food_0001_candidate.py"},
        "verification_required_before_approval": [
            f"Open {LABEL_URL} and confirm section {SECTION_TITLE} reads as the evidence text.",
            "Confirm generated food guidance stays within supported_claim (a risk factor with monitoring, "
            "not an instruction to avoid).",
        ],
        "how_to_approve": ("Copy the three files into data/live_medical/relationships/v2/food_0001/ (each approved "
                           "V2 dataset has its own folder; never copy over another dataset's files), and set status "
                           "to APPROVED and approval to {\"approved_by\": \"<name>\", \"approved_at\": \"<YYYY-MM-DD>\"}."),
    }
    (OUT / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"chunk_id": CHUNK_ID, "content_hash": content_hash, "spl_version": version,
                      "chars": len(text)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
