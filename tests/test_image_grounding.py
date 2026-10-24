"""Image-text grounding of vision-suggested medication names (services/image_grounding.py).

Matching and OCR-status rules run on fixed OCR text. One test runs the real Windows OCR engine on synthetic
images and is skipped on other platforms. No real prescription or patient data is used.
"""

from __future__ import annotations

import io
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image, ImageDraw, ImageFont

from adaptive_trust_medical_rag.services import image_grounding
from adaptive_trust_medical_rag.services.image_grounding import (
    OCR_ERROR,
    OCR_OK,
    OCR_STOPPED,
    OCR_UNAVAILABLE,
    ImageText,
    ground_candidates,
)

REAL_RECOGNIZER = image_grounding.recognize_image_text  # bound before conftest replaces it per test


def cand(raw, normalized=None, confidence="HIGH"):
    return SimpleNamespace(raw_text=raw, normalized_text=normalized, confidence=SimpleNamespace(value=confidence))


def read(*lines):
    return ImageText(OCR_OK, "\n".join(lines), "fixture-ocr")


def kept_names(candidates, image_text):
    kept, _ = ground_candidates(candidates, image_text)
    return [(c.raw_text, span) for c, span in kept]


# ── Blank or unreadable images ────────────────────────────────────────────────

def test_a_high_confidence_name_on_a_blank_image_is_withheld():
    kept, withheld = ground_candidates([cand("Acetaminophen", "acetaminophen")], read())
    assert kept == [] and withheld[0][1] == "the name does not appear in the image text"


@pytest.mark.parametrize("status", [OCR_UNAVAILABLE, OCR_ERROR])
def test_when_the_image_text_cannot_be_read_nothing_is_kept(status):
    kept, withheld = ground_candidates([cand("Warfarin 5mg", "warfarin")], ImageText(status, reason="x"))
    assert kept == [] and withheld[0][1] == f"the image text could not be read ({status.lower()})"


# ── Name matching ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("candidate, text, span", [
    (cand("Warfarin 5mg", "warfarin"), "WARFARIN 5MG TABLET", "WARFARIN"),             # case; the confirmed name
    (cand("Toprol-XL"), "Toprol XL 50 mg once daily", "Toprol XL"),                    # punctuation
    (cand("Warfarin", "warfarin"), "Rx: Coumadin 5 mg", "Coumadin"),                   # brand on the label
    (cand("Advil"), "Ibuprofen 200 mg as needed", "Ibuprofen"),                         # generic on the label
])
def test_case_punctuation_and_cached_aliases_match_whole_words(candidate, text, span):
    assert kept_names([candidate], read(text)) == [(candidate.raw_text, span)]


@pytest.mark.parametrize("candidate, text", [
    (cand("Hydroxyzine"), "Hydralazine 25 mg"),                 # similar but different drug
    (cand("Celebrex"), "Celexa 20 mg"),
    (cand("Warfarin"), "Warfarinex 5 mg"),                      # name inside an unrelated word
    (cand("Aspirin"), "Paspirine syrup"),
    (cand("Metoprolol succinate"), "Lopressor 50 mg"),          # brand of a different salt
])
def test_similar_embedded_or_other_salt_names_do_not_match(candidate, text):
    assert kept_names([candidate], read(text)) == []


def test_a_truncated_name_in_the_image_does_not_ground_the_full_name_the_user_would_confirm():
    # Live 2026-10-23: the image read "Warf... 5 mg"; the model completed it. The user confirms "warfarin",
    # which the image never shows, so the model's raw "Warf... 5 mg" cannot vouch for it.
    candidates = [cand("Warf... 5 mg", "warfarin"), cand("Ibupr... 400 mg", "ibuprofen")]
    assert kept_names(candidates, read("Warf... 5 mg tablet - once daily", "Ibupr... 400 mg - as needed")) == []


@pytest.mark.parametrize("name", ["5", "mg", "5 mg", "x 1"])
def test_a_name_with_fewer_than_three_letters_is_never_grounded(name):
    # A dose or unit is printed on every prescription; it is not evidence of a medication name.
    kept, withheld = ground_candidates([cand(name)], read("Warfarin 5 mg tablet x 1"))
    assert kept == [] and withheld[0][1] == "the name is too short to verify"


def test_a_brand_missing_from_the_local_alias_list_is_withheld():
    # "Tylenol" is not in data/drug_entity_cache.json, so the printed brand cannot ground "acetaminophen".
    assert kept_names([cand("Tylenol 500 mg", "acetaminophen")], read("Tylenol 500 mg tablets")) == []


@pytest.mark.parametrize("name", ["NSAIDs", "ACE inhibitors", "Statins"])
def test_a_drug_class_is_never_kept_as_one_medication(name):
    kept, withheld = ground_candidates([cand(name)], read(f"Avoid {name} with this medicine"))
    assert kept == [] and withheld[0][1] == "a drug class, not one medication"


def test_of_two_candidates_only_the_one_in_the_image_text_is_kept():
    kept, withheld = ground_candidates([cand("Warfarin 5mg", "warfarin"), cand("Acetaminophen", "acetaminophen")],
                                       read("Warfarin 5mg tablet once daily"))
    assert [c.raw_text for c, _ in kept] == ["Warfarin 5mg"]
    assert [c.raw_text for c, _ in withheld] == ["Acetaminophen"]


# ── The OCR engine ────────────────────────────────────────────────────────────

def test_other_platforms_report_ocr_unavailable(monkeypatch):
    monkeypatch.setattr(image_grounding.sys, "platform", "linux")
    assert REAL_RECOGNIZER(b"img", "image/png").status == OCR_UNAVAILABLE


def finished_process(seen, stdout=b"", returncode=0):
    """A Popen stand-in for an OCR process that has already exited; records how it was started."""
    def popen(args, **kwargs):
        seen.update(kwargs["env"], args=args, kwargs=kwargs)
        return SimpleNamespace(returncode=returncode, communicate=lambda timeout=None: (stdout, b""))
    return popen


def test_the_ocr_child_process_gets_no_secrets_no_shell_and_no_user_data_in_its_command(monkeypatch):
    seen = {}
    monkeypatch.setattr(image_grounding.sys, "platform", "win32")
    monkeypatch.setattr(image_grounding.subprocess, "Popen", finished_process(seen))
    monkeypatch.setenv("GROQ_API_KEY", "test-secret-value")
    assert REAL_RECOGNIZER(b"img", "image/x-evil;$(calc)").status == OCR_OK
    assert "test-secret-value" not in seen.values() and "GROQ_API_KEY" not in seen
    assert "OCR_IMAGE_PATH" in seen and not os.path.exists(seen["OCR_IMAGE_PATH"])  # the temp image is gone
    args, kwargs = seen["args"], seen["kwargs"]
    assert Path(args[0]).is_absolute() and args[0].lower().endswith("powershell.exe")
    assert args[1:4] == ["-NoProfile", "-NonInteractive", "-EncodedCommand"] and len(args) == 5
    assert "shell" not in kwargs
    assert seen["OCR_IMAGE_PATH"].endswith("upload.img")  # an unknown MIME type never reaches the path


@pytest.mark.parametrize("error", [OSError("no exe"), ValueError("embedded null byte")])
def test_an_ocr_invocation_failure_is_an_error_without_details_and_leaves_no_temp_file(monkeypatch, error):
    seen = {}

    def popen(args, **kwargs):
        seen.update(kwargs["env"])
        raise error
    monkeypatch.setattr(image_grounding.sys, "platform", "win32")
    monkeypatch.setattr(image_grounding.subprocess, "Popen", popen)
    result = REAL_RECOGNIZER(b"img", "image/png")
    assert (result.status, result.reason, result.text) == (OCR_ERROR, type(error).__name__, "")
    assert not os.path.exists(seen["OCR_IMAGE_PATH"])


def test_malformed_ocr_output_grounds_nothing(monkeypatch):
    monkeypatch.setattr(image_grounding.sys, "platform", "win32")
    monkeypatch.setattr(image_grounding.subprocess, "Popen",
                        finished_process({}, stdout=b"\xff\xfe\x00\x81W\x00a\x00r\x00f"))
    text = REAL_RECOGNIZER(b"img", "image/png")
    assert text.status == OCR_OK and kept_names([cand("Warfarin", "warfarin")], text) == []


def recognize_in_thread(stop=None, image=b"img"):
    """Runs the recognizer in a worker thread, as the pipeline does; -> (thread, result dict)."""
    result = {}
    worker = threading.Thread(target=lambda: result.update(text=REAL_RECOGNIZER(image, "image/png", stop=stop)))
    worker.start()
    return worker, result


def wait_for(condition, seconds=10):
    deadline = time.monotonic() + seconds
    while not condition():
        assert time.monotonic() < deadline, "timed out"
        time.sleep(0.01)


def test_a_stop_request_kills_the_running_ocr_process_and_removes_its_image(endless_ocr_process):
    stop = threading.Event()
    worker, result = recognize_in_thread(stop)
    wait_for(lambda: endless_ocr_process)
    t0 = time.monotonic()
    stop.set()
    worker.join(10)
    (proc, image_path), = endless_ocr_process
    assert not worker.is_alive() and time.monotonic() - t0 < 5  # not the 30 s timeout
    assert (result["text"].status, result["text"].text) == (OCR_STOPPED, "")  # not an OCR error
    assert proc.poll() is not None  # the operating-system process has exited
    assert not os.path.exists(image_path)


def test_an_ocr_process_past_its_timeout_is_killed_and_reported_as_an_error(monkeypatch, endless_ocr_process):
    monkeypatch.setattr(image_grounding, "OCR_TIMEOUT_S", 0.5)
    result = REAL_RECOGNIZER(b"img", "image/png")
    (proc, image_path), = endless_ocr_process
    assert (result.status, result.reason) == (OCR_ERROR, "TimeoutExpired")
    assert proc.poll() is not None and not os.path.exists(image_path)


def test_a_stop_requested_before_the_ocr_starts_starts_no_process(endless_ocr_process):
    stop = threading.Event()
    stop.set()
    assert REAL_RECOGNIZER(b"img", "image/png", stop=stop).status == OCR_STOPPED
    assert endless_ocr_process == []


def test_a_failed_process_cleanup_is_logged_without_paths_or_data(monkeypatch, caplog):
    class Unkillable:  # never exits, and refuses to be killed
        returncode = None

        def communicate(self, timeout=None):
            raise subprocess.TimeoutExpired("ocr", timeout)

        def kill(self):
            raise PermissionError(r"Access is denied: C:\Users\someone\AppData\Local\Temp\tmpabc\upload.png")
    started = []
    monkeypatch.setattr(image_grounding.sys, "platform", "win32")
    monkeypatch.setattr(image_grounding.subprocess, "Popen", lambda args, **kwargs: started.append(1) or Unkillable())
    stop = threading.Event()
    with caplog.at_level(logging.INFO, logger=image_grounding.__name__):
        worker, out = recognize_in_thread(stop)
        wait_for(lambda: started)
        stop.set()
        worker.join(10)
    assert not worker.is_alive() and out["text"].status == OCR_STOPPED
    assert "OCR process cleanup failed: PermissionError" in caplog.text
    assert "tmpabc" not in caplog.text and "someone" not in caplog.text


def _png(lines=()):
    img = Image.new("RGB", (900, 120 + 90 * len(lines)), "white")
    if lines:
        draw, font = ImageDraw.Draw(img), ImageFont.truetype(str(Path(os.environ["SystemRoot"]) / "Fonts" / "arial.ttf"), 36)
        for i, line in enumerate(lines):
            draw.text((40, 40 + i * 90), line, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.mark.skipif(sys.platform != "win32", reason="the Windows OCR engine exists only on Windows")
def test_the_real_windows_ocr_reads_nothing_from_a_blank_image_and_the_lines_of_a_synthetic_one():
    blank = REAL_RECOGNIZER(_png(), "image/png")
    assert (blank.status, blank.text) == (OCR_OK, "")
    rx = REAL_RECOGNIZER(_png(["SYNTHETIC TEST PRESCRIPTION", "Warfarin 5 mg tablet"]), "image/png")
    assert rx.status == OCR_OK and "Warfarin 5 mg tablet" in rx.text
    assert kept_names([cand("Warfarin", "warfarin"), cand("Acetaminophen")], rx) == [("Warfarin", "Warfarin")]
    assert REAL_RECOGNIZER(b"not an image", "image/png").status == OCR_ERROR


@pytest.mark.skipif(sys.platform != "win32", reason="the Windows OCR engine exists only on Windows")
def test_a_stop_request_ends_the_real_powershell_ocr_process(monkeypatch):
    """PowerShell runs WinRT OCR in-process and starts no child process (checked with process snapshots
    on 2026-10-23), so ending this one process ends all of the OCR work."""
    started, real_popen = [], subprocess.Popen

    def popen(args, **kwargs):  # the real PowerShell OCR command, only recorded
        proc = real_popen(args, **kwargs)
        started.append((proc, kwargs["env"]["OCR_IMAGE_PATH"]))
        return proc
    monkeypatch.setattr(image_grounding.subprocess, "Popen", popen)
    stop = threading.Event()
    worker, result = recognize_in_thread(stop, _png(["SYNTHETIC TEST PRESCRIPTION", "Warfarin 5 mg tablet"]))
    wait_for(lambda: started)
    stop.set()
    worker.join(10)
    (proc, image_path), = started
    assert not worker.is_alive() and result["text"].status == OCR_STOPPED
    assert proc.poll() is not None and not os.path.exists(image_path)
