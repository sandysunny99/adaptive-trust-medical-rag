import asyncio
import os

import pytest


@pytest.fixture(autouse=True)
def _set_default_llm_mode(monkeypatch):
    if not os.environ.get("LLM_MODE"):
        monkeypatch.setenv("LLM_MODE", "DETERMINISTIC_MOCK")


@pytest.fixture(autouse=True)
def _no_real_ocr(monkeypatch):
    """Tests never run the real Windows OCR by default: it reads nothing, so image candidates fail closed.

    A test that needs image text sets ``image_text_recognizer`` on the app state with ``ocr_reads``.
    """
    from adaptive_trust_medical_rag.services import image_grounding
    monkeypatch.setattr(image_grounding, "recognize_image_text",
                        lambda image_bytes, mime, stop=None: image_grounding.ImageText(
                            image_grounding.OCR_UNAVAILABLE, reason="tests use ocr_reads"))


@pytest.fixture
def endless_ocr_process(monkeypatch):
    """The real OCR code path, with a real child process that never finishes in place of PowerShell.

    Returns the list of (process, image path) the OCR code started, so a test can check the operating
    system process exited and the temporary image is gone. The code's own Popen arguments (minimal
    environment, pipes) are kept; only the command is replaced.
    """
    import subprocess
    import sys

    from adaptive_trust_medical_rag.services import image_grounding
    started, real_popen = [], subprocess.Popen

    def popen(args, **kwargs):
        if not str(args[0]).lower().endswith("powershell.exe"):  # only the OCR command is replaced
            return real_popen(args, **kwargs)
        proc = real_popen([sys.executable, "-c", "import time; time.sleep(60)"], **kwargs)
        started.append((proc, kwargs["env"]["OCR_IMAGE_PATH"]))
        return proc
    monkeypatch.setattr(image_grounding.sys, "platform", "win32")
    monkeypatch.setattr(image_grounding.subprocess, "Popen", popen)
    yield started
    for proc, _ in started:  # never leave a child behind, whatever the test did
        if proc.poll() is None:
            proc.kill()
            proc.wait(5)


@pytest.fixture
def ocr_reads():
    """Factory for a deterministic OCR stand-in: the image 'reads' exactly the given lines (none = blank)."""
    from adaptive_trust_medical_rag.services import image_grounding

    def make(*lines):
        text = "\n".join(lines)
        return lambda image_bytes, mime: image_grounding.ImageText(image_grounding.OCR_OK, text, "fixture-ocr")
    return make


async def stream_and_confirm_async(client, app, request_id, payload, *, timeout=30.0):
    """Open the analysis stream and confirm once the request waits for it, as the UI does.

    /confirm refuses a confirmation before extraction has finished, so a flow that confirms must
    first see the request reach confirmation. Returns (confirm response or None, stream response).
    """
    stream = asyncio.create_task(client.get(f"/api/v1/stream/{request_id}"))
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout
    while not (app.state.pending_analyses.get(request_id) or {}).get("awaiting_confirmation"):
        if stream.done() or loop.time() > deadline:
            return None, await stream
        await asyncio.sleep(0.01)
    confirm = await client.post(f"/api/v1/analyze/{request_id}/confirm", json=payload)
    return confirm, await stream


@pytest.fixture
def extraction_finished():
    """Put a pending request in the state the pipeline leaves it in after extraction (route-level tests)."""
    def mark(app, request_id):
        analysis = app.state.pending_analyses[request_id]
        analysis.setdefault("confirmation_event", asyncio.Event())
        analysis["awaiting_confirmation"] = True
        return analysis
    return mark


@pytest.fixture
def stream_and_confirm():
    """Synchronous form for TestClient tests: (app, request_id, payload) -> (confirm, stream)."""
    from httpx import ASGITransport, AsyncClient

    def run(app, request_id, payload, **kwargs):
        async def flow():
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                return await stream_and_confirm_async(client, app, request_id, payload, **kwargs)
        return asyncio.run(flow())
    return run
