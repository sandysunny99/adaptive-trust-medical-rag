"""The deployed app serves the built frontend from / with a page CSP; API responses stay deny-all."""

import os

os.environ.setdefault("TESTING", "1")

from fastapi.testclient import TestClient  # noqa: E402

from adaptive_trust_medical_rag.api import app as app_module  # noqa: E402


def test_built_frontend_is_served_with_page_csp(tmp_path, monkeypatch):
    dist = tmp_path / "frontend" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>t</title>", encoding="utf-8")
    monkeypatch.setattr(app_module, "REPO_ROOT", tmp_path)

    client = TestClient(app_module.create_app())
    page = client.get("/")
    assert page.status_code == 200
    assert "script-src" not in page.headers["content-security-policy"]  # falls back to default-src 'self'
    assert page.headers["content-security-policy"].startswith("default-src 'self'")

    api = client.get("/api/v1/llm/models")
    assert api.status_code == 200
    assert api.headers["content-security-policy"] == "default-src 'none'"


def test_no_frontend_mount_without_a_build(tmp_path, monkeypatch):
    monkeypatch.setattr(app_module, "REPO_ROOT", tmp_path)
    assert TestClient(app_module.create_app()).get("/").status_code == 404
