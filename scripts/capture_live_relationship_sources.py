"""Capture the exact source documents behind the live relationship candidate.

Run this on a machine that can reach DailyMed and RxNav (the researcher's machine; the cloud
environment cannot). It downloads, byte for byte:

- each prescribing-information SPL document (XML) by DailyMed set ID, with its version history;
- each medication's RxNav properties record by RxCUI.

It writes a capture manifest with every URL, HTTP status, size, SHA-256 and the UTC time. It
parses nothing and decides nothing: the candidate relationship record is built from these bytes
afterwards and stays CANDIDATE_PENDING_RESEARCHER_APPROVAL until a named researcher approves it.
These are free public endpoints; no credentials are used.

    python scripts/capture_live_relationship_sources.py [--out DIR]

The output folder carries its own .gitignore, so the raw downloads are never committed by
accident. The frozen corpus and research data are not touched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "data" / "live_medical" / "relationships" / "source_capture"

# Labels identified on 2026-10-14 for REL-LIVE-0001 (simvastatin and clarithromycin).
SPL_SOURCES = (
    {"setid": "8f55d5de-5a4f-4a39-8c84-c53976dd6af9", "drug": "simvastatin",
     "label_seen": "ZOCOR- simvastatin tablet, film coated (Organon LLC), Revised 8/2023"},
    {"setid": "9aaffb41-408c-4372-8fd5-1d649450c0e9", "drug": "clarithromycin",
     "label_seen": "CLARITHROMYCIN tablet, film coated (Aurobindo Pharma Limited), Revised 10/2023"},
)
RXCUIS = ("36567", "21212")  # simvastatin, clarithromycin

DAILYMED = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls"
RXNAV = "https://rxnav.nlm.nih.gov/REST/rxcui"


def planned_downloads() -> list[dict[str, str]]:
    items = []
    for spl in SPL_SOURCES:
        items.append({"kind": "spl_xml", "id": spl["setid"], "drug": spl["drug"], "label_seen": spl["label_seen"],
                      "url": f"{DAILYMED}/{spl['setid']}.xml", "file": f"spl_{spl['setid']}.xml"})
        items.append({"kind": "spl_history", "id": spl["setid"], "drug": spl["drug"],
                      "url": f"{DAILYMED}/{spl['setid']}/history.json", "file": f"spl_{spl['setid']}_history.json"})
    for rxcui in RXCUIS:
        items.append({"kind": "rxnav_properties", "id": rxcui,
                      "url": f"{RXNAV}/{rxcui}/properties.json", "file": f"rxnav_{rxcui}_properties.json"})
    return items


def capture(out_dir: Path, client: httpx.Client) -> dict:
    """Download every planned item into out_dir; the manifest records each outcome."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / ".gitignore").write_text("# Raw source downloads; never committed.\n*\n", encoding="utf-8")
    entries, failed = [], 0
    for item in planned_downloads():
        entry = dict(item, fetched_at=datetime.now(UTC).isoformat())
        try:
            response = client.get(item["url"])
            entry["http_status"] = response.status_code
            if response.status_code != 200 or not response.content:
                raise ValueError(f"HTTP {response.status_code}, {len(response.content)} bytes")
            (out_dir / item["file"]).write_bytes(response.content)
            entry.update(bytes=len(response.content), sha256=hashlib.sha256(response.content).hexdigest(),
                         content_type=response.headers.get("content-type"), status="CAPTURED")
        except (httpx.HTTPError, ValueError) as e:
            failed += 1
            entry.update(status="FAILED", error=f"{type(e).__name__}: {e}")
            entry.pop("file", None)
        entries.append(entry)

    manifest = {
        "purpose": "Exact source capture for live relationship candidate REL-LIVE-0001 (simvastatin, clarithromycin)",
        "captured_at": datetime.now(UTC).isoformat(),
        "status": "COMPLETE" if failed == 0 else "INCOMPLETE",
        "failed": failed,
        "items": entries,
        "note": "Raw bytes only. Nothing here is approved evidence; approval is a separate researcher decision.",
    }
    (out_dir / "CAPTURE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=None,
                        help=f"output folder (default: {DEFAULT_OUT.relative_to(ROOT)}/<UTC date>)")
    args = parser.parse_args(argv)
    out_dir = args.out or DEFAULT_OUT / datetime.now(UTC).strftime("%Y-%m-%d")
    with httpx.Client(timeout=30.0, follow_redirects=True,
                      headers={"User-Agent": "adaptive-trust-medical-rag source capture"}) as client:
        manifest = capture(out_dir, client)
    for entry in manifest["items"]:
        print(f"{entry['status']:9} {entry['kind']:17} {entry['id']}  {entry.get('sha256', entry.get('error'))}")
    print(f"{manifest['status']}: {out_dir}")
    return 0 if manifest["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    sys.exit(main())
