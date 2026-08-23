#!/usr/bin/env python
"""CI: Smoke test the FastAPI /health endpoint."""

import sys

sys.path.insert(0, "src")

from fastapi.testclient import TestClient

from adaptive_trust_medical_rag.api.app import create_app

app = create_app()
client = TestClient(app)
resp = client.get("/health")

if resp.status_code != 200:
    print(f"FAIL - /health returned {resp.status_code}")
    sys.exit(1)

data = resp.json()
for field in ("status", "version"):
    if field not in data:
        print(f"FAIL - Missing field: {field}")
        sys.exit(1)

print(f"OK - API health: {data['status']} v{data['version']}")
