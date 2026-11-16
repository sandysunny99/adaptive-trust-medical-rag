"""Prepare the REL-LIVE V2 candidate from the captured clarithromycin label (pending files only).

Reads the byte-exact capture, writes into <out_dir> only, never into data/live_medical/.
Usage: python build_v2_candidate.py <repo_root> <capture_dir> <out_dir>
"""
import hashlib
import html
import json
import re
import sys
from pathlib import Path

repo, capture, out = (Path(p) for p in sys.argv[1:4])
sys.path.insert(0, str(repo / "src"))
from adaptive_trust_medical_rag.services.live_relationships import validate_record  # noqa: E402

out.mkdir(parents=True, exist_ok=False)
manifest = json.loads((capture / "CAPTURE_MANIFEST.json").read_text(encoding="utf-8"))
items = {i["file"]: i for i in manifest["items"]}
XML = "spl_9aaffb41-408c-4372-8fd5-1d649450c0e9.xml"
xml = (capture / XML).read_bytes()
assert hashlib.sha256(xml).hexdigest() == items[XML]["sha256"], "capture hash mismatch"
START, END = 75723, 76181
raw_span = xml[START:END]
assert raw_span.startswith(b"<paragraph>") and raw_span.endswith(b"</paragraph>")
# Plain text: tags removed, entities unescaped, every whitespace run (including the NBSP after "see") -> one space.
text = re.sub(r"\s+", " ", html.unescape(re.sub(rb"<[^>]+>", b"", raw_span).decode("utf-8"))).strip()
section_title = re.sub(rb"<[^>]+>", b"", xml[xml.rfind(b"<title", 0, START):START]).decode().split("\n")[0].strip()
set_id = "9aaffb41-408c-4372-8fd5-1d649450c0e9"
version = re.search(rb'<versionNumber value="(\d+)"', xml).group(1).decode()
effective = re.search(rb'<effectiveTime value="(\d+)"', xml).group(1).decode()
rx = {f: json.loads((capture / f).read_text(encoding="utf-8"))["properties"]
      for f in ("rxnav_36567_properties.json", "rxnav_21212_properties.json")}
assert rx["rxnav_36567_properties.json"]["name"] == "simvastatin" and rx["rxnav_21212_properties.json"]["name"] == "clarithromycin"

chunk_id = f"DAILYMED-SPL-{set_id}-V{version}-S4.5-P1"
document_id = f"SPL-{set_id}-V{version}"
content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

from sentence_transformers import SentenceTransformer  # noqa: E402
embedding = SentenceTransformer("all-MiniLM-L6-v2").encode(text).tolist()  # same call as scripts/build_live_corpus_v2.py

chunk = {
    "chunk_id": chunk_id,
    "document_id": document_id,
    "document_title": f"CLARITHROMYCIN tablet, film coated (Aurobindo Pharma Limited), SPL v{version}, section {section_title}",
    "document_url": f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={set_id}",
    "source_type": "DAILYMED",
    "text": text,
    "content_hash": content_hash,
    "embedding": embedding,
    "embedding_model": "all-MiniLM-L6-v2",
    "provenance": {
        "source": "DAILYMED",
        "spl_set_id": set_id,
        "spl_version": version,
        "spl_effective_time": effective,
        "section": section_title,
        "capture_url": items[XML]["url"],
        "captured_at": items[XML]["fetched_at"],
        "capture_file_sha256": items[XML]["sha256"],
        "capture_file_bytes": items[XML]["bytes"],
        "byte_start": START,
        "byte_end": END,
        "raw_span_sha256": hashlib.sha256(raw_span).hexdigest(),
        "text_derivation": "XML tags removed, HTML entities unescaped, each whitespace run (incl. U+00A0) replaced by one space, trimmed",
    },
    "status": "CANDIDATE_PENDING_RESEARCHER_APPROVAL",
}
record = {
    "record_id": "REL-LIVE-0002",
    "supersedes_candidate": "REL-LIVE-0001",
    "subject": {"name": "simvastatin", "rxcui": "36567"},
    "object": {"name": "clarithromycin", "rxcui": "21212"},
    "predicate": "CONTRAINDICATION",
    "direction": "BIDIRECTIONAL",
    "severity": "CONTRAINDICATED",
    "source_chunk_id": chunk_id,
    "source_document_id": document_id,
    "source_document_url": chunk["document_url"],
    "source_content_hash": content_hash,
    "evidence_span": text,
}
records = {"dataset_version": "LIVE_RELATIONSHIP_RECORDS_V2_CANDIDATE", "corpus_version": "LIVE_MEDICAL_CORPUS_V2 + LIVE_EVIDENCE_SUPPLEMENT_V2_CANDIDATE", "records": [record]}
records_raw = (json.dumps(records, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
(out / "LIVE_RELATIONSHIP_RECORDS_V2_CANDIDATE.json").write_bytes(records_raw)
(out / "LIVE_EVIDENCE_SUPPLEMENT_V2_CANDIDATE.json").write_text(json.dumps([chunk], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

valid_with_supplement = validate_record(record, {chunk_id: chunk})[1]
frozen = json.loads((repo / "data/live_medical/LIVE_MEDICAL_CORPUS_V2.json").read_text(encoding="utf-8"))
valid_against_frozen = validate_record(record, {c["chunk_id"]: c for c in frozen})[1]

mf = {
    "dataset_version": "LIVE_RELATIONSHIP_RECORDS_V2_CANDIDATE",
    "records_file": "LIVE_RELATIONSHIP_RECORDS_V2_CANDIDATE.json",
    "records_sha256": hashlib.sha256(records_raw.replace(b"\r\n", b"\n")).hexdigest(),
    "evidence_supplement_file": "LIVE_EVIDENCE_SUPPLEMENT_V2_CANDIDATE.json",
    "status": "CANDIDATE_PENDING_RESEARCHER_APPROVAL",
    "approval": None,
    "prepared": {"by": "Claude (AI-prepared candidate; not a reviewer)", "on": "2026-10-15",
                 "method": "Evidence span read from the byte-exact DailyMed SPL capture at the recorded offsets; content hash and embedding recomputed locally."},
    "rxnav": {f.split("_")[1]: {k: v[k] for k in ("rxcui", "name", "tty", "suppress")} for f, v in rx.items()},
    "validation": {
        "validate_record_against_supplement_chunk": valid_with_supplement,
        "validate_record_against_frozen_corpus_only": valid_against_frozen,
    },
    "not_active": "Not under data/live_medical/relationships/. The production loader reads only LIVE_RELATIONSHIP_RECORDS_V1 and requires the source chunk to be in LIVE_MEDICAL_CORPUS_V2, so this candidate cannot load. Activating it needs the researcher's approval and a separate, reviewed decision on how the supplement chunk enters retrieval without changing the frozen corpus.",
    "review_points": [
        "Confirm the plain-text evidence span against section 4.5 of the clarithromycin label (setid above, version and effective date above).",
        "Confirm direction BIDIRECTIONAL: the span is the clarithromycin label contraindicating co-administration with simvastatin; the ZOCOR label (setid 8f55d5de-..., captured v11, effectiveTime 20250328) contraindicates strong CYP3A4 inhibitors and names clarithromycin only in the Table 2 Examples row.",
        "Decide whether the label version captured (v21, 20231010) is the one to cite.",
    ],
}
(out / "LIVE_RELATIONSHIP_RECORDS_V2_CANDIDATE_MANIFEST.json").write_text(json.dumps(mf, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"chunk_id": chunk_id, "content_hash": content_hash, "raw_span_sha256": chunk["provenance"]["raw_span_sha256"],
                  "records_sha256": mf["records_sha256"], "embedding_dims": len(embedding), "text": text,
                  "validation": mf["validation"]}, indent=2, ensure_ascii=False))
