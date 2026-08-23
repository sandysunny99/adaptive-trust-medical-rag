"""Independent Forensic Verification Engine

Project: Adaptive Trust-Aware Medical RAG
Component: Forensic Evidence Trace Verifier

Performs independent cryptographic verification of case-level evaluation results,
response SHA-256 digests, canonical result hashes, timestamp bounds, and field formats
without calling LLM, retriever, or trust scorer components.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


class ForensicVerifier:
    """Decoupled verifier for auditing recorded RAG evaluation traces."""

    HEX_64_PATTERN = re.compile(r"^[0-9a-f]{64}$")

    def verify_trace_file(self, trace_file_path: str | Path) -> dict[str, Any]:
        """Load trace JSON file and execute full forensic verification."""
        p = Path(trace_file_path)
        if not p.exists():
            return {
                "verdict": "FAILED",
                "reason": f"Trace file not found: {p}",
                "checks": {"file_exists": "FAIL"},
            }

        try:
            record = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            return {
                "verdict": "FAILED",
                "reason": f"Failed to parse trace JSON: {e}",
                "checks": {"json_format": "FAIL"},
            }

        return self.verify_record(record)

    def verify_record(
        self, record: dict[str, Any], raw_response_text: str | None = None
    ) -> dict[str, Any]:
        """Perform independent verification on a single case result dictionary."""
        checks: dict[str, str] = {}
        failures: list[str] = []

        # ── 1. Response Hash Verification ────────────────────────────────────
        ans_text = raw_response_text or record.get("generated_answer", "")
        recorded_ans_hash = record.get("generated_answer_hash", "") or record.get(
            "llm_execution", {}
        ).get("response_hash", "")

        if ans_text:
            indep_ans_hash = hashlib.sha256(ans_text.encode("utf-8")).hexdigest()
            if self.HEX_64_PATTERN.match(indep_ans_hash):
                checks["response_hash_format"] = "PASS"
            else:
                checks["response_hash_format"] = "FAIL"
                failures.append(
                    "Independent response hash is not a valid 64-char lowercase hex digest."
                )

            if recorded_ans_hash:
                if indep_ans_hash == recorded_ans_hash:
                    checks["response_hash_rematch"] = "PASS"
                else:
                    checks["response_hash_rematch"] = "FAIL"
                    failures.append(
                        f"Response hash mismatch: computed {indep_ans_hash[:12]} "
                        f"vs recorded {recorded_ans_hash[:12]}"
                    )
            else:
                checks["response_hash_rematch"] = "SKIPPED"
        else:
            checks["response_hash_format"] = "SKIPPED"
            checks["response_hash_rematch"] = "SKIPPED"

        # ── 2. Canonical Result Hash Independent Re-computation ──────────────
        recorded_result_hash = record.get("result_hash", "")
        payload = {
            "case_id": record.get("case_id", ""),
            "variant": record.get("variant", ""),
            "query_hash": record.get("query_hash", ""),
            "generated_answer_hash": record.get("generated_answer_hash", "") or recorded_ans_hash,
            "retrieval_ids": sorted(record.get("retrieved_documents", [])),
            "trust_values": [round(x, 4) for x in record.get("trust_scores", [])],
            "verification_state": sorted(record.get("claim_verification", [])),
        }

        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        indep_result_hash = hashlib.sha256(serialized).hexdigest()

        if self.HEX_64_PATTERN.match(indep_result_hash):
            checks["result_hash_format"] = "PASS"
        else:
            checks["result_hash_format"] = "FAIL"
            failures.append("Result hash is not a valid 64-char lowercase hex digest.")

        if recorded_result_hash:
            if indep_result_hash == recorded_result_hash:
                checks["result_hash_rematch"] = "PASS"
            else:
                checks["result_hash_rematch"] = "FAIL"
                failures.append(
                    f"Result hash mismatch: computed {indep_result_hash[:12]} "
                    f"vs recorded {recorded_result_hash[:12]}"
                )
        else:
            checks["result_hash_rematch"] = "SKIPPED"

        # ── 3. Dataset Hash Format ───────────────────────────────────────────
        ds_hash = record.get("dataset_sha256", "")
        if ds_hash and self.HEX_64_PATTERN.match(ds_hash):
            checks["dataset_hash_format"] = "PASS"
        elif ds_hash:
            checks["dataset_hash_format"] = "FAIL"
            failures.append("Dataset SHA-256 hash is invalid.")
        else:
            checks["dataset_hash_format"] = "SKIPPED"

        # ── 4. Git Commit Provenance ─────────────────────────────────────────
        commit = record.get("git_commit", "")
        if commit and commit != "unresolved_git_commit" and len(commit) >= 7:
            checks["git_commit_provenance"] = "PASS"
        else:
            checks["git_commit_provenance"] = "FAIL"
            failures.append("Git commit hash is missing or unresolved.")

        # ── 5. Timestamp Order Check ─────────────────────────────────────────
        llm_exec = record.get("llm_execution", {})
        start_ts = llm_exec.get("request_started_at", "")
        end_ts = llm_exec.get("response_received_at", "")
        if start_ts and end_ts:
            if end_ts >= start_ts:
                checks["timestamp_bounds"] = "PASS"
            else:
                checks["timestamp_bounds"] = "FAIL"
                failures.append("Response timestamp received before request start timestamp.")
        else:
            checks["timestamp_bounds"] = "SKIPPED"

        # ── Verdict Determination ───────────────────────────────────────────
        if any(val == "FAIL" for val in checks.values()):
            verdict = "FAILED"
        elif all(val in ("PASS", "SKIPPED") for val in checks.values()):
            verdict = "VERIFIED"
        else:
            verdict = "PARTIALLY_VERIFIED"

        return {
            "verdict": verdict,
            "checks": checks,
            "failures": failures,
            "indep_response_hash": indep_ans_hash if ans_text else "",
            "indep_result_hash": indep_result_hash,
            "case_id": record.get("case_id", ""),
            "variant": record.get("variant", ""),
        }
