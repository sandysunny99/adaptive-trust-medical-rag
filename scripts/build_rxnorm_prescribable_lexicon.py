#!/usr/bin/env python3
"""Build the offline medication-name lexicon from NLM's RxNorm Current Prescribable Content.

Source: the Prescribable RxNorm API (https://rxnav.nlm.nih.gov/REST/Prescribe/), NLM's own interface to the
Current Prescribable Content subset (SAB=RXNORM, active concepts only, no UMLS licence required; NLM: "provides
this subset without any licensing restrictions"). The release zip (download.nlm.nih.gov) was not reachable from
the build machine on 2026-10-27, so the API is used; its data version is recorded and must equal the intended
monthly release.

Writes, into a new folder data/terminology/rxnorm_prescribable_<release>/ (never overwritten):
  source/version.json, source/allconcepts_<TTY>.json  the API responses, byte for byte
  MEDICATION_LEXICON_V1.json                          {"format", "release", "entries": [{"rxcui","name","tty"}]}
  MANIFEST.json                                       release, endpoints, SHA-256 of every file, counts, terms

Term types: IN (ingredient), PIN (precise ingredient, e.g. a salt), MIN (multiple ingredients), BN (brand name).
They are kept apart; the application never treats one as another. The lexicon is single-line JSON, so its
SHA-256 does not depend on a checkout's line endings. Run by hand for a reviewed release; never at runtime.

Usage:  python scripts/build_rxnorm_prescribable_lexicon.py --expect-release 05-Oct-2026
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
API = "https://rxnav.nlm.nih.gov/REST"
TTYS = ("IN", "PIN", "MIN", "BN")
ATTRIBUTION = "This product uses publicly available data from the U.S. National Library of Medicine (NLM)."


def fetch(url: str) -> bytes:
    if not url.startswith(API + "/"):
        raise ValueError(f"only {API} is fetched, not {url}")
    with urllib.request.urlopen(url, timeout=60) as r:  # noqa: S310  # nosec B310 - https NLM API only, checked above
        return r.read()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--expect-release", required=True, help='data version the API must report, e.g. "05-Oct-2026"')
    args = parser.parse_args()

    version_raw = fetch(f"{API}/version.json")
    release = json.loads(version_raw)["version"]
    if release != args.expect_release:
        print(f"API reports release {release!r}, expected {args.expect_release!r}; nothing written.", file=sys.stderr)
        return 1
    stamp = datetime.strptime(release, "%d-%b-%Y").strftime("%Y-%m-%d")
    out = REPO / "data" / "terminology" / f"rxnorm_prescribable_{stamp}"
    if out.exists():
        print(f"{out} exists; a release folder is never overwritten.", file=sys.stderr)
        return 1

    raw = {"version.json": version_raw}
    entries = []
    for tty in TTYS:
        body = fetch(f"{API}/Prescribe/allconcepts.json?tty={tty}")
        raw[f"allconcepts_{tty}.json"] = body
        for c in json.loads(body)["minConceptGroup"]["minConcept"]:
            if c["tty"] != tty:
                raise ValueError(f"{tty} response holds a {c['tty']} concept: {c}")
            entries.append({"rxcui": c["rxcui"], "name": c["name"], "tty": tty})
        time.sleep(1)  # NLM asks for at most 20 requests per second
    if json.loads(fetch(f"{API}/version.json"))["version"] != release:
        print("The API release changed during the build; nothing written.", file=sys.stderr)
        return 1

    entries.sort(key=lambda e: (e["tty"], e["name"], e["rxcui"]))
    lexicon = json.dumps({"format": "rxnorm-prescribable-lexicon/1", "release": release, "entries": entries},
                         ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    (out / "source").mkdir(parents=True)
    for name, body in raw.items():
        (out / "source" / name).write_bytes(body)
    (out / "MEDICATION_LEXICON_V1.json").write_bytes(lexicon)
    manifest = {
        "lexicon": "MEDICATION_LEXICON_V1.json",
        "lexicon_sha256": sha256(lexicon),
        "format": "rxnorm-prescribable-lexicon/1",
        "release": release,
        "publisher": "U.S. National Library of Medicine (NLM)",
        "subset": "RxNorm Current Prescribable Content (SAB=RXNORM; active concepts)",
        "subset_documentation": "https://www.nlm.nih.gov/research/umls/rxnorm/docs/prescribe.html",
        "retrieved_via": f"{API}/Prescribe/allconcepts.json?tty=<TTY>; release from {API}/version.json",
        "retrieved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "term_types": {"IN": "ingredient", "PIN": "precise ingredient (salt or other form)",
                       "MIN": "multiple ingredients", "BN": "brand name"},
        "counts": {tty: sum(e["tty"] == tty for e in entries) for tty in TTYS} | {"entries": len(entries),
                                                                                  "distinct_rxcui": len({e["rxcui"] for e in entries})},
        "source_files_sha256": {f"source/{name}": sha256(body) for name, body in raw.items()},
        "terms": "NLM: no licence required for the Current Prescribable Content subset; RxNav APIs are subject to "
                 "https://lhncbc.nlm.nih.gov/RxNav/TermsofService.html (at most 20 requests/s; attribution; the NLM "
                 "name and logo may not be used).",
        "attribution": ATTRIBUTION,
        "scope_limits": "US prescribable and many OTC drugs; excludes suppressed, obsolete, foreign-only and "
                        "veterinary-only drugs. Not every medication name is present.",
        "generator": "scripts/build_rxnorm_prescribable_lexicon.py",
    }
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"folder": str(out.relative_to(REPO)), "lexicon_sha256": manifest["lexicon_sha256"],
                      "counts": manifest["counts"]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
