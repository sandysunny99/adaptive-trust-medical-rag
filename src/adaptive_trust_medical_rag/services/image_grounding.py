"""Independent image-text evidence for the medication names a vision model suggests.

A vision model's confidence is not evidence that a name is in the image: on 2026-10-22 one returned
"Acetaminophen" with HIGH confidence for a blank white image. Its own transcription comes from the same
response, so it cannot confirm the name either. Here a separate engine (the built-in Windows OCR: local,
no upload, no new dependency) reads the image, and a candidate is kept only when its name, or a cached
alias of the same generic, appears in that text as whole words. Kept candidates still need the user's
explicit confirmation; text evidence says the name is printed, not that the prescription is correct.
"""

from __future__ import annotations

import base64
import functools
import logging
import os
import re
import subprocess  # nosec B404 - runs only the fixed Windows OCR script below
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from adaptive_trust_medical_rag.normalization.entity_cache import EntityCache
from adaptive_trust_medical_rag.verification.canonical_identity import names_drug_class

log = logging.getLogger(__name__)

OCR_OK, OCR_UNAVAILABLE, OCR_ERROR, OCR_STOPPED = "OK", "UNAVAILABLE", "ERROR", "STOPPED"
OCR_ENGINE = "windows.media.ocr"
OCR_TIMEOUT_S = 30
# How often a running OCR process is checked for a stop request.
OCR_POLL_S = 0.1


@dataclass(frozen=True)
class ImageText:
    """What an OCR engine read. ``reason`` explains UNAVAILABLE or ERROR and never holds image content."""

    status: str
    text: str = ""
    engine: str | None = None
    reason: str | None = None


# Reads $env:OCR_IMAGE_PATH and prints one recognised line per output line (UTF-8). Exit 1 on any failure.
_WINDOWS_OCR_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
try {
  [Console]::OutputEncoding = [Text.Encoding]::UTF8
  Add-Type -AssemblyName System.Runtime.WindowsRuntime
  $null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
  $null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
  $null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]
  $asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
  function Await($op, [Type]$type) { $t = $asTask.MakeGenericMethod($type).Invoke($null, @($op)); $t.Wait(); $t.Result }
  $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($env:OCR_IMAGE_PATH)) ([Windows.Storage.StorageFile])
  $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
  if ($null -eq $engine) { exit 1 }
  $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
  foreach ($line in $result.Lines) { [Console]::WriteLine($line.Text) }
  $stream.Dispose()
} catch { exit 1 }
"""
_SUFFIX = {"image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/webp": ".webp",
           "image/bmp": ".bmp", "image/gif": ".gif", "image/tiff": ".tif"}


def recognize_image_text(image_bytes: bytes, mime: str, stop: threading.Event | None = None) -> ImageText:
    """Read the image's text with the built-in Windows OCR engine; UNAVAILABLE on other platforms.

    Setting ``stop`` (from another thread) kills the OCR process within about ``OCR_POLL_S`` and
    returns STOPPED once it has exited; its temporary image is then removed. A process still running
    after ``OCR_TIMEOUT_S`` is killed the same way and reported as an ERROR.
    """
    if sys.platform != "win32":
        return ImageText(OCR_UNAVAILABLE, reason="no local OCR engine on this platform")
    if stop is not None and stop.is_set():
        return ImageText(OCR_STOPPED, engine=OCR_ENGINE, reason="stopped before it started")
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    powershell = Path(system_root) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    script = base64.b64encode(_WINDOWS_OCR_SCRIPT.encode("utf-16-le")).decode("ascii")
    # A file the OCR still locks must not turn a finished read into an exception (Windows).
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        path = Path(tmp) / f"upload{_SUFFIX.get(mime, '.img')}"
        path.write_bytes(image_bytes)
        # Only what PowerShell needs: no API keys or other secrets reach the child process.
        env = {k: os.environ[k] for k in ("SystemRoot", "windir", "SystemDrive", "USERPROFILE", "TEMP", "TMP")
               if k in os.environ} | {"OCR_IMAGE_PATH": str(path)}
        try:
            proc = subprocess.Popen(  # nosec B603 - fixed executable path and script; the image path is our temp file
                [str(powershell), "-NoProfile", "-NonInteractive", "-EncodedCommand", script],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        except Exception as e:  # no executable, bad environment: never the details
            return ImageText(OCR_ERROR, engine=OCR_ENGINE, reason=type(e).__name__)
        deadline = time.monotonic() + OCR_TIMEOUT_S
        while True:
            try:
                stdout, _ = proc.communicate(timeout=OCR_POLL_S)  # retrying loses no output
                break
            except subprocess.TimeoutExpired:
                stopped = stop is not None and stop.is_set()
                if stopped or time.monotonic() >= deadline:
                    _end(proc)  # before the temporary image is removed, which the process may hold open
                    if stopped:
                        return ImageText(OCR_STOPPED, engine=OCR_ENGINE, reason="stopped")
                    return ImageText(OCR_ERROR, engine=OCR_ENGINE, reason="TimeoutExpired")
            except Exception as e:  # never the details
                _end(proc)
                return ImageText(OCR_ERROR, engine=OCR_ENGINE, reason=type(e).__name__)
    if proc.returncode != 0:
        return ImageText(OCR_ERROR, engine=OCR_ENGINE, reason=f"OCR exited with code {proc.returncode}")
    return ImageText(OCR_OK, stdout.decode("utf-8", "replace").strip(), OCR_ENGINE)


def _end(proc: subprocess.Popen) -> None:
    """Kill the OCR process and wait for it to exit (Windows has no gentler stop); never raises."""
    try:
        proc.kill()
        proc.communicate(timeout=5)
        log.info("OCR process stopped (exit code %s)", proc.returncode)
    except Exception as e:  # already gone, or still running after 5 s: the type only, no paths or data
        log.warning("OCR process cleanup failed: %s", type(e).__name__)


@functools.lru_cache(maxsize=1)
def _alias_cache() -> EntityCache:
    return EntityCache.load_default()


def _whole_words(name: str) -> re.Pattern[str] | None:
    """The name as whole words, any punctuation or spacing between them ("Toprol-XL" = "toprol xl")."""
    words = re.findall(r"[A-Za-z0-9]+", name)
    if not words:
        return None
    return re.compile(r"(?<![A-Za-z0-9])" + r"[^A-Za-z0-9]+".join(map(re.escape, words)) + r"(?![A-Za-z0-9])",
                      re.IGNORECASE)


def _accepted_names(candidate: Any, cache: EntityCache) -> list[str]:
    """The name the user would confirm (normalised name, else raw text) and its cached brand/generic aliases.

    Only that name counts: the model's raw text cannot vouch for it, so a truncated "Warf..." in the image
    never grounds "warfarin".
    """
    presented = (candidate.normalized_text or candidate.raw_text or "").strip()
    if not presented:
        return []
    entry = cache.lookup(presented)
    return [presented] + (cache.names_for_generic(str(entry["generic_name"]))
                          if entry and entry.get("generic_name") else [])


def ground_candidates(candidates: list[Any], image_text: ImageText,
                      cache: EntityCache | None = None) -> tuple[list[tuple[Any, str]], list[tuple[Any, str]]]:
    """Split vision candidates into (kept, withheld).

    Kept: (candidate, the OCR text span that names it). Withheld: (candidate, why). Nothing is kept
    unless the OCR engine actually read the image; a drug class is never kept as one medication.
    """
    if image_text.status != OCR_OK:
        return [], [(c, f"the image text could not be read ({image_text.status.lower()})") for c in candidates]
    cache = cache if cache is not None else _alias_cache()
    kept, withheld = [], []
    for c in candidates:
        if any(names_drug_class(n) for n in (c.raw_text, c.normalized_text) if n):
            withheld.append((c, "a drug class, not one medication"))
            continue
        if len(re.findall(r"[A-Za-z]", c.normalized_text or c.raw_text or "")) < 3:
            withheld.append((c, "the name is too short to verify"))  # a dose or unit is on every prescription
            continue
        span = next((m.group(0) for n in _accepted_names(c, cache)
                     if (p := _whole_words(n)) and (m := p.search(image_text.text))), None)
        if span:
            kept.append((c, span))
        else:
            withheld.append((c, "the name does not appear in the image text"))
    return kept, withheld
