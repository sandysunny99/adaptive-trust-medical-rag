"""Revision 2 of the REL-LIVE-0002 candidate, in the layout the V2 loader reads (pending files only).

Takes revision 1 (relationship_v2_candidate/) and writes <out_dir> with:
  LIVE_RELATIONSHIP_RECORDS_V2.json, LIVE_RELATIONSHIP_EVIDENCE_V2.json, LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json
The record, the evidence text, its hash and its embedding are unchanged. Added to the chunk:
authority 0.95 and freshness 0.9 (the values the frozen corpus gives its DailyMed chunks) and
provenance.content_hash, which the retrieval-time integrity check reads.
Usage: python build_v2_candidate_r2.py <r1_dir> <out_dir>
"""
import hashlib
import json
import sys
from pathlib import Path

r1, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=False)
m1 = json.loads((r1 / "LIVE_RELATIONSHIP_RECORDS_V2_CANDIDATE_MANIFEST.json").read_text(encoding="utf-8"))
recs = json.loads((r1 / m1["records_file"]).read_text(encoding="utf-8"))
(chunk,) = json.loads((r1 / m1["evidence_supplement_file"]).read_text(encoding="utf-8"))

chunk = dict(chunk)
chunk.pop("status", None)
chunk["authority"] = 0.95
chunk["freshness"] = 0.9
chunk["provenance"] = dict(chunk["provenance"], content_hash=chunk["content_hash"], chunk_id=chunk["chunk_id"],
                           document_id=chunk["document_id"])
recs["dataset_version"] = "LIVE_RELATIONSHIP_RECORDS_V2"
recs["corpus_version"] = "LIVE_MEDICAL_CORPUS_V2 + LIVE_RELATIONSHIP_EVIDENCE_V2"

records_raw = (json.dumps(recs, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
evidence_raw = (json.dumps([chunk], indent=2, ensure_ascii=False) + "\n").encode("utf-8")
(out / "LIVE_RELATIONSHIP_RECORDS_V2.json").write_bytes(records_raw)
(out / "LIVE_RELATIONSHIP_EVIDENCE_V2.json").write_bytes(evidence_raw)
lf = lambda b: hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest()  # noqa: E731
manifest = {
    "dataset_version": "LIVE_RELATIONSHIP_RECORDS_V2",
    "records_file": "LIVE_RELATIONSHIP_RECORDS_V2.json",
    "records_sha256": lf(records_raw),
    "evidence_file": "LIVE_RELATIONSHIP_EVIDENCE_V2.json",
    "evidence_sha256": lf(evidence_raw),
    "hash_note": "SHA-256 with CRLF normalised to LF, as for V1.",
    "status": "CANDIDATE_PENDING_RESEARCHER_APPROVAL",
    "approval": None,
    "prepared": {"by": "Claude (AI-prepared candidate; not a reviewer)", "on": "2026-10-15", "revision": 2,
                 "method": "Revision 1 converted to the V2 loader layout; record, text, content hash and embedding unchanged; authority 0.95 and freshness 0.9 added to match the frozen corpus's DailyMed chunks."},
    "rxnav": m1["rxnav"],
    "use_in_application": "None while pending. Once APPROVED with approved_by and approved_at, and placed in data/live_medical/relationships/, the V2 loader accepts the record, adds the evidence chunk to retrieval and gives it the record's identity; the frozen corpus is not changed.",
    "review_points": m1["review_points"] + [
        "Confirm authority 0.95 and freshness 0.9 for this label (the frozen corpus uses these values for DailyMed).",
        "The record states a contraindication of co-administration only; it does not verify any mechanism or adverse-effect claim beyond the span.",
    ],
}
(out / "LIVE_RELATIONSHIP_RECORDS_V2_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: manifest[k] for k in ("records_sha256", "evidence_sha256", "status", "approval")}, indent=2))
