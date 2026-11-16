"""Build the REL-LIVE-0002 review package (copies and derived text only; candidate files are not changed).

Usage: python build_review_package.py <repo> <run_dir> <capture_dir> <package_dir>
"""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

repo, run, cap, pkg = (Path(p) for p in sys.argv[1:5])
r1, r2 = run / "relationship_v2_candidate", run / "relationship_v2_candidate_r2"
sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731
lf = lambda b: sha(b.replace(b"\r\n", b"\n"))  # noqa: E731

# 1. Exact copies of every candidate file (r1 = files under review, r2 = same content in loader layout).
for src_dir, tag in ((r1, "r1"), (r2, "r2")):
    dest = pkg / f"files_{tag}"
    dest.mkdir()
    for f in sorted(src_dir.glob("*.json")):
        shutil.copy2(f, dest / f.name)


def abbreviated(obj):
    """The same JSON with each embedding vector replaced by a description (length, dtype, sha256)."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k == "embedding" and isinstance(v, list):
                raw = json.dumps(v).encode()
                out[k] = f"<ABBREVIATED: {len(v)} float values (JSON numbers, float32 model output), sha256 of json.dumps(vector) {sha(raw)}>"
            else:
                out[k] = abbreviated(v)
        return out
    if isinstance(obj, list):
        return [abbreviated(x) for x in obj]
    return obj


for tag, d in (("r1", r1), ("r2", r2)):
    for f in sorted(d.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        (pkg / f"text_{tag}_{f.stem}.json").write_text(json.dumps(abbreviated(data), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# 2. Recomputed hashes and the byte range.
m1 = json.loads((r1 / "LIVE_RELATIONSHIP_RECORDS_V2_CANDIDATE_MANIFEST.json").read_text(encoding="utf-8"))
m2 = json.loads((r2 / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").read_text(encoding="utf-8"))
capm = json.loads((cap / "CAPTURE_MANIFEST.json").read_text(encoding="utf-8"))
(c1,) = json.loads((r1 / m1["evidence_supplement_file"]).read_text(encoding="utf-8"))
(c2,) = json.loads((r2 / m2["evidence_file"]).read_text(encoding="utf-8"))
rec1 = json.loads((r1 / m1["records_file"]).read_text(encoding="utf-8"))["records"][0]
rec2 = json.loads((r2 / m2["records_file"]).read_text(encoding="utf-8"))["records"][0]
xml_item = next(i for i in capm["items"] if i["kind"] == "spl_xml" and i["drug"] == "clarithromycin")
xml = (cap / xml_item["file"]).read_bytes()
p = c1["provenance"]
span = xml[p["byte_start"]:p["byte_end"]]
(pkg / "extracted_byte_range_75723-76181.xml.txt").write_bytes(span)
lines = []
add = lines.append
add("# Recomputed hashes (2026-10-17)")
add(f"captured XML {xml_item['file']}: bytes {len(xml)} sha256 {sha(xml)}  (CAPTURE_MANIFEST: bytes {xml_item['bytes']} sha256 {xml_item['sha256']})")
add(f"byte range [{p['byte_start']}, {p['byte_end']}) = {len(span)} bytes, sha256 {sha(span)}  (recorded raw_span_sha256 {p['raw_span_sha256']})")
add(f"chunk text sha256 {sha(c1['text'].encode('utf-8'))}  (recorded content_hash {c1['content_hash']}; record source_content_hash {rec1['source_content_hash']})")
add(f"r1 records file LF sha256 {lf((r1 / m1['records_file']).read_bytes())}  (manifest records_sha256 {m1['records_sha256']})")
add(f"r2 records file LF sha256 {lf((r2 / m2['records_file']).read_bytes())}  (manifest {m2['records_sha256']})")
add(f"r2 evidence file LF sha256 {lf((r2 / m2['evidence_file']).read_bytes())}  (manifest {m2['evidence_sha256']})")
add("")
add("# r1 vs r2")
add(f"record identical apart from nothing: {rec1 == rec2}")
add(f"evidence text identical: {c1['text'] == c2['text']}; content_hash identical: {c1['content_hash'] == c2['content_hash']}; embedding identical: {c1['embedding'] == c2['embedding']}")
add(f"r2 adds: authority {c2['authority']}, freshness {c2['freshness']}, provenance.content_hash {c2['provenance']['content_hash'] == c2['content_hash']}")
add(f"approval fields: r1 status {m1['status']} approval {m1['approval']}; r2 status {m2['status']} approval {m2['approval']}")
add("")
add("# Extracted text of the byte range (tags removed, entities unescaped, whitespace collapsed)")
add(c1["text"])
add("")
add("# RxNav responses (captured files, verbatim)")
for f in ("rxnav_36567_properties.json", "rxnav_21212_properties.json"):
    add(f"{f}: {(cap / f).read_text(encoding='utf-8').strip()}")
add("")
add("# CAPTURE_MANIFEST entries (verbatim)")
add(json.dumps({k: capm[k] for k in ("purpose", "captured_at", "status", "failed")}, indent=2))
for item in capm["items"]:
    add(json.dumps(item, indent=2))
(pkg / "hashes_byte_range_rxnav_capture.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
shutil.copy2(cap / "CAPTURE_MANIFEST.json", pkg / "CAPTURE_MANIFEST.copy.json")
print("\n".join(lines[:16]))
