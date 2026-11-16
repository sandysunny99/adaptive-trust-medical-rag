import hashlib, json, re, sys, html
sc = sys.argv[1]
m = json.load(open(f"{sc}/CAPTURE_MANIFEST.json", encoding="utf-8"))
for it in m["items"]:
    b = open(f"{sc}/{it['file']}", "rb").read()
    print(it["file"], "bytes_ok", len(b) == it["bytes"], "sha_ok", hashlib.sha256(b).hexdigest() == it["sha256"])
x = open(f"{sc}/spl_9aaffb41-408c-4372-8fd5-1d649450c0e9.xml", "rb").read()
span = x[75723:76181]
print("span_sha256", hashlib.sha256(span).hexdigest(), "len", len(span))
print("raw_has_tags", b"<" in span)
txt = html.unescape(re.sub(rb"<[^>]+>", b"", span).decode("utf-8"))
print("SPAN_TEXT:", re.sub(r"\s+", " ", txt))
print("BEFORE:", x[75723-60:75723])
print("AFTER:", x[76181:76181+40])
for tag in (b"<setId", b"<versionNumber", b"<effectiveTime"):
    i = x.find(tag); print(x[i:i+90])
pre = x[:75723]
for _ in range(3):
    j = pre.rfind(b"<title")
    print("preceding_title:", re.sub(rb"<[^>]+>", b"", x[j:j+250]).decode(errors="replace").strip()[:120])
    pre = pre[:j]
for f in ("rxnav_36567_properties.json", "rxnav_21212_properties.json"):
    print(open(f"{sc}/{f}", encoding="utf-8").read())
