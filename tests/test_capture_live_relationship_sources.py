"""The source-capture script stores exact bytes with hashes and never reports a partial capture as complete."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import httpx

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "capture_live_relationship_sources.py"
spec = importlib.util.spec_from_file_location("capture_live_relationship_sources", SCRIPT)
capture_script = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture_script)


def client(fail_url: str | None = None) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == fail_url:
            return httpx.Response(404, content=b"not found")
        return httpx.Response(200, content=f"body of {request.url}".encode(), headers={"content-type": "text/plain"})
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_every_source_is_stored_byte_for_byte_with_its_hash(tmp_path):
    manifest = capture_script.capture(tmp_path, client())
    assert manifest["status"] == "COMPLETE" and manifest["failed"] == 0
    kinds = sorted(e["kind"] for e in manifest["items"])
    assert kinds == ["rxnav_properties"] * 2 + ["spl_history"] * 2 + ["spl_xml"] * 2
    for entry in manifest["items"]:
        data = (tmp_path / entry["file"]).read_bytes()
        assert data == f"body of {entry['url']}".encode()
        assert entry["sha256"] == hashlib.sha256(data).hexdigest()
        assert entry["url"].startswith(("https://dailymed.nlm.nih.gov/", "https://rxnav.nlm.nih.gov/"))
    assert json.loads((tmp_path / "CAPTURE_MANIFEST.json").read_text(encoding="utf-8")) == manifest
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8").strip().endswith("*")


def test_a_failed_download_makes_the_capture_incomplete(tmp_path):
    failing = f"{capture_script.RXNAV}/21212/properties.json"
    manifest = capture_script.capture(tmp_path, client(fail_url=failing))
    assert manifest["status"] == "INCOMPLETE" and manifest["failed"] == 1
    (bad,) = [e for e in manifest["items"] if e["status"] == "FAILED"]
    assert bad["url"] == failing and "404" in bad["error"] and "file" not in bad
    assert not (tmp_path / "rxnav_21212_properties.json").exists()


def test_the_sources_are_the_labels_identified_for_the_candidate():
    assert {s["drug"] for s in capture_script.SPL_SOURCES} == {"simvastatin", "clarithromycin"}
    assert capture_script.RXCUIS == ("36567", "21212")
