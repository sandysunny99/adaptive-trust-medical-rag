"""Independent review of the REL-LIVE-0002 candidate files against the byte-exact capture.

Does not import the builder. Prints one PASS/FAIL line per check and exits 1 on any FAIL.
Usage: python review_v2_candidate.py <repo_root> <capture_dir> <candidate_dir>
"""
import hashlib
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

repo, cap, cand = (Path(p) for p in sys.argv[1:4])
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))


sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731
mf = json.loads((cand / "LIVE_RELATIONSHIP_RECORDS_V2_CANDIDATE_MANIFEST.json").read_text(encoding="utf-8"))
rec_raw = (cand / mf["records_file"]).read_bytes()
recs = json.loads(rec_raw.decode("utf-8"))
chunks = json.loads((cand / mf["evidence_supplement_file"]).read_text(encoding="utf-8"))
capm = json.loads((cap / "CAPTURE_MANIFEST.json").read_text(encoding="utf-8"))

# Manifest state
check("manifest status is CANDIDATE_PENDING_RESEARCHER_APPROVAL", mf["status"] == "CANDIDATE_PENDING_RESEARCHER_APPROVAL", mf["status"])
check("manifest approval is null (no reviewer, no time)", mf["approval"] is None)
check("records_sha256 (LF-normalised) matches the records file", sha(rec_raw.replace(b"\r\n", b"\n")) == mf["records_sha256"], mf["records_sha256"][:12])
check("exactly one record and one chunk", len(recs["records"]) == 1 and len(chunks) == 1)
r, c = recs["records"][0], chunks[0]

# Capture files
for item in capm["items"]:
    b = (cap / item["file"]).read_bytes()
    check(f"capture {item['file']} bytes+sha256 match CAPTURE_MANIFEST", len(b) == item["bytes"] and sha(b) == item["sha256"])
xml_item = next(i for i in capm["items"] if i["kind"] == "spl_xml" and i["drug"] == "clarithromycin")
xml = (cap / xml_item["file"]).read_bytes()
p = c["provenance"]
check("chunk provenance capture sha256 = captured XML", p["capture_file_sha256"] == sha(xml) == xml_item["sha256"])
check("chunk provenance capture URL = captured URL", p["capture_url"] == xml_item["url"])

# XML metadata, parsed with an XML parser rather than regex
root = ET.fromstring(xml)
ns = {"v3": "urn:hl7-org:v3"}
set_id = root.find("v3:setId", ns).get("root")
version = root.find("v3:versionNumber", ns).get("value")
eff = root.find("v3:effectiveTime", ns).get("value")
check("setId = 9aaffb41-408c-4372-8fd5-1d649450c0e9", set_id == "9aaffb41-408c-4372-8fd5-1d649450c0e9" == p["spl_set_id"], set_id)
check("SPL version 21 recorded", version == "21" == p["spl_version"], version)
check("effectiveTime 20231010 recorded", eff == "20231010" == p["spl_effective_time"], eff)
check("document URL is the official DailyMed page for that setid (https)",
      c["document_url"] == r["source_document_url"] == f"https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid={set_id}")

# Byte span
span = xml[p["byte_start"]:p["byte_end"]]
check("byte offsets 75723-76181", (p["byte_start"], p["byte_end"]) == (75723, 76181))
check("raw span sha256 recorded correctly", sha(span) == p["raw_span_sha256"], p["raw_span_sha256"][:12])
check("raw span is exactly one <paragraph> element", span.startswith(b"<paragraph>") and span.endswith(b"</paragraph>") and span.count(b"<paragraph") == 1)

# The span's section, via the XML tree: find the section whose text contains the span text
para_text = None
for sec in root.iter("{urn:hl7-org:v3}section"):
    title = sec.find("v3:title", ns)
    if title is not None and "".join(title.itertext()).strip().startswith("4.5"):
        for para in sec.iter("{urn:hl7-org:v3}paragraph"):
            t = re.sub(r"\s+", " ", "".join(para.itertext())).strip()
            if "simvastatin" in t:
                para_text = t
        sec_title = "".join(title.itertext()).strip()
        break
check("section 4.5 found by XML parse", para_text is not None, sec_title if para_text else "")
check("plain text (independent XML-parser extraction) == chunk text", para_text == c["text"])
check("record evidence_span == chunk text", r["evidence_span"] == c["text"])
check("chunk content_hash = sha256(text)", sha(c["text"].encode("utf-8")) == c["content_hash"] == r["source_content_hash"], c["content_hash"][:12])
check("record source_chunk_id = chunk_id", r["source_chunk_id"] == c["chunk_id"])
t = c["text"].lower()
check("span names simvastatin and clarithromycin as whole words", bool(re.search(r"\bsimvastatin\b", t) and re.search(r"\bclarithromycin\b", t)))
check("span states the combination is contraindicated", "concomitant administration" in t and "is contraindicated" in t)

# Identities
rx = {f: json.loads((cap / f).read_text(encoding="utf-8"))["properties"] for f in ("rxnav_36567_properties.json", "rxnav_21212_properties.json")}
check("RxNav 36567 = simvastatin, IN, not suppressed", (rx["rxnav_36567_properties.json"]["name"], rx["rxnav_36567_properties.json"]["tty"], rx["rxnav_36567_properties.json"]["suppress"]) == ("simvastatin", "IN", "N"))
check("RxNav 21212 = clarithromycin, IN, not suppressed", (rx["rxnav_21212_properties.json"]["name"], rx["rxnav_21212_properties.json"]["tty"], rx["rxnav_21212_properties.json"]["suppress"]) == ("clarithromycin", "IN", "N"))
check("record subject 36567 simvastatin / object 21212 clarithromycin",
      (r["subject"], r["object"]) == ({"name": "simvastatin", "rxcui": "36567"}, {"name": "clarithromycin", "rxcui": "21212"}))
check("predicate CONTRAINDICATION, severity CONTRAINDICATED, direction BIDIRECTIONAL",
      (r["predicate"], r["severity"], r["direction"]) == ("CONTRAINDICATION", "CONTRAINDICATED", "BIDIRECTIONAL"))

# Embedding, recomputed
emb = c["embedding"]
check("embedding has 384 dimensions, model all-MiniLM-L6-v2", len(emb) == 384 and c.get("embedding_model") == "all-MiniLM-L6-v2")
from sentence_transformers import SentenceTransformer  # noqa: E402
fresh = SentenceTransformer("all-MiniLM-L6-v2").encode(c["text"]).tolist()
cos = sum(a * b for a, b in zip(emb, fresh)) / (math.sqrt(sum(a * a for a in emb)) * math.sqrt(sum(b * b for b in fresh)))
check("embedding reproduces (cosine >= 0.9999)", cos >= 0.9999, f"cosine {cos:.6f}")

# Not active, frozen corpus untouched
frozen = json.loads((repo / "data/live_medical/LIVE_MEDICAL_CORPUS_V2.json").read_text(encoding="utf-8"))
check("chunk_id not already in the frozen corpus", c["chunk_id"] not in {x["chunk_id"] for x in frozen})
check("no V2 candidate file under data/live_medical/", not list((repo / "data/live_medical").rglob("*V2_CANDIDATE*")))

print(f"\n{sum(results)} of {len(results)} checks passed")
sys.exit(0 if all(results) else 1)
