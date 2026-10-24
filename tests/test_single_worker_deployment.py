"""The backend's supported deployment: one uvicorn worker (analysis requests live in process memory).

An upload, its stream, its confirmation and its cancel must reach the same process, so a second worker
would break them silently. The documented command is run for real: with one worker it serves, and the
same command with two workers refuses to start.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from adaptive_trust_medical_rag.api.app import requested_workers

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("argv, env, expected", [
    (["uvicorn", "app:app"], {}, 1),
    (["uvicorn", "app:app", "--workers", "1"], {}, 1),
    (["uvicorn", "app:app", "--workers", "4"], {}, 4),
    (["uvicorn", "app:app", "--workers=2"], {}, 2),
    (["uvicorn", "app:app"], {"WEB_CONCURRENCY": "3"}, 3),
    (["uvicorn", "app:app", "--workers", "1"], {"WEB_CONCURRENCY": "3"}, 1),  # the option wins, as in uvicorn
])
def test_the_requested_worker_count_is_read_as_uvicorn_reads_it(argv, env, expected):
    assert requested_workers(argv, env) == expected


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def launch(workers: int | None, port: int, web_concurrency: str | None = None) -> subprocess.Popen:
    """The documented backend command (README), with the given ``--workers`` (None: the option left out)."""
    env = {k: v for k, v in os.environ.items() if k != "WEB_CONCURRENCY"} | {"TESTING": "1"}
    if web_concurrency is not None:
        env["WEB_CONCURRENCY"] = web_concurrency
    return subprocess.Popen(  # noqa: S603 - fixed argv, test-only
        [sys.executable, "-m", "uvicorn", "--app-dir", "src", "adaptive_trust_medical_rag.api.app:app",
         "--host", "127.0.0.1", "--port", str(port)] + (["--workers", str(workers)] if workers else []),
        cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def test_the_documented_single_worker_command_serves():
    port = free_port()
    server = launch(1, port)
    try:
        deadline = time.monotonic() + 120
        while True:
            assert server.poll() is None, server.stdout.read().decode("utf-8", "replace")[-2000:]
            try:
                if httpx.get(f"http://127.0.0.1:{port}/health", timeout=2).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            assert time.monotonic() < deadline, "the server did not start"
            time.sleep(0.5)
    finally:
        server.kill()
        server.wait(15)


@pytest.mark.parametrize("workers, web_concurrency", [(2, None), (None, "2")], ids=["--workers 2", "WEB_CONCURRENCY=2"])
def test_the_same_command_with_two_workers_refuses_to_start(workers, web_concurrency):
    server = launch(workers, free_port(), web_concurrency)
    try:
        output, _ = server.communicate(timeout=180)
    finally:
        if server.poll() is None:
            server.kill()
            server.wait(15)
    text = output.decode("utf-8", "replace")
    # It ended by itself: every worker refused, so uvicorn stopped the parent (which exits with 0).
    assert "supports one worker; it was started with 2" in text
    assert "failed to start, stopping the parent process" in text
