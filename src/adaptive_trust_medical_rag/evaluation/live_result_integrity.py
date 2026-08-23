"""Automated Live Result Integrity Auditor

Project: Adaptive Trust-Aware Medical RAG
Component: Live Experiment Result Integrity Auditor

Audits multi-case live experiment runs (e.g., 20 cases × 6 variants = 120 executions),
verifying provenance, independent response/result SHA-256 hashes, ablation component
execution integrity, response variability, failure rate thresholds, and zero mock leakage.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


class LiveResultIntegrityAuditor:
    """Audits live experiment runs for evidence integrity, determinism, and runtime correctness."""

    HEX_64_PATTERN = re.compile(r"^[0-9a-f]{64}$")

    def audit_run_directory(self, run_dir_path: str | Path) -> dict[str, Any]:
        """Load case_results.jsonl from run directory and execute complete audit."""
        p = Path(run_dir_path)
        jsonl_file = p / "case_results.jsonl"
        if not jsonl_file.exists():
            return {
                "verdict": "FAIL",
                "reason": f"case_results.jsonl not found in {p}",
                "records_audited": 0,
                "failure_rate": 1.0,
            }

        records = []
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))

        return self.audit_records(records)

    def audit_records(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        """Perform comprehensive integrity audit on list of live variant result records."""
        if not records:
            return {
                "verdict": "FAIL",
                "reason": "No execution records provided for audit.",
                "records_audited": 0,
                "failure_rate": 1.0,
            }

        total_records = len(records)
        failed_count = 0
        checks: dict[str, str] = {}
        anomalies: list[str] = []

        # ── 1. Mock / Simulation Leakage Check ─────────────────────────────
        mock_leaks = 0
        for rec in records:
            backend = str(rec.get("execution_backend", "")).lower()
            exec_type = str(rec.get("execution_type", "")).lower()
            if "mock" in backend or "simulation" in exec_type or not rec.get("runtime_verified"):
                mock_leaks += 1
        if mock_leaks == 0:
            checks["no_mock_leakage"] = "PASS"
        else:
            checks["no_mock_leakage"] = "FAIL"
            anomalies.append(f"Mock/simulation leakage detected in {mock_leaks} live records.")
            failed_count += mock_leaks

        # ── 2. Provenance & Hashes Check ────────────────────────────────────
        hash_mismatches = 0
        format_errors = 0
        for rec in records:
            # Recompute response hash
            ans_text = rec.get("generated_answer", "")
            rec_ans_hash = rec.get("generated_answer_hash", "") or rec.get("llm_execution", {}).get(
                "response_hash", ""
            )
            if ans_text:
                indep_ans_hash = hashlib.sha256(ans_text.encode("utf-8")).hexdigest()
                if rec_ans_hash and indep_ans_hash != rec_ans_hash:
                    hash_mismatches += 1
                if not self.HEX_64_PATTERN.match(indep_ans_hash):
                    format_errors += 1

            # Recompute result hash
            payload = {
                "case_id": rec.get("case_id", ""),
                "variant": rec.get("variant", ""),
                "query_hash": rec.get("query_hash", ""),
                "generated_answer_hash": rec.get("generated_answer_hash", "") or rec_ans_hash,
                "retrieval_ids": sorted(rec.get("retrieved_documents", [])),
                "trust_values": [round(x, 4) for x in rec.get("trust_scores", [])],
                "verification_state": sorted(rec.get("claim_verification", [])),
            }
            serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
            indep_result_hash = hashlib.sha256(serialized).hexdigest()
            rec_result_hash = rec.get("result_hash", "")

            if rec_result_hash and indep_result_hash != rec_result_hash:
                hash_mismatches += 1
            if not self.HEX_64_PATTERN.match(indep_result_hash):
                format_errors += 1

        if hash_mismatches == 0 and format_errors == 0:
            checks["cryptographic_hashes"] = "PASS"
        else:
            checks["cryptographic_hashes"] = "FAIL"
            anomalies.append(
                f"{hash_mismatches} hash mismatches and {format_errors} format errors detected."
            )
            failed_count += hash_mismatches + format_errors

        # ── 3. Response Variability Check ───────────────────────────────────
        response_hashes = [
            rec.get("generated_answer_hash", "")
            for rec in records
            if rec.get("generated_answer_hash")
        ]
        unique_resp_hashes = set(response_hashes)
        if len(records) > 5 and len(unique_resp_hashes) <= 1:
            checks["response_variability"] = "WARN"
            anomalies.append(
                "All execution records produced identical response hashes (suspicious uniformity)."
            )
        else:
            checks["response_variability"] = "PASS"

        # ── 4. Ablation Component Runtime Integrity Check ──────────────────
        variant_runtime_errors = 0
        for rec in records:
            v = rec.get("variant", "")
            ret_exec = rec.get("retrieval_execution", {})
            trust_exec = rec.get("trust_execution", {})
            verif_exec = rec.get("verification_execution", {})

            if v == "A" and ret_exec.get("dense_called"):
                variant_runtime_errors += 1
            elif v == "B" and not ret_exec.get("dense_called"):
                variant_runtime_errors += 1
            elif v == "C" and not (ret_exec.get("dense_called") and ret_exec.get("bm25_called")):
                variant_runtime_errors += 1
            elif v == "D" and not ret_exec.get("graph_called"):
                variant_runtime_errors += 1
            elif v == "E" and not trust_exec.get("called"):
                variant_runtime_errors += 1
            elif v == "F" and not (trust_exec.get("called") and verif_exec.get("called")):
                variant_runtime_errors += 1

        if variant_runtime_errors == 0:
            checks["ablation_runtime_integrity"] = "PASS"
        else:
            checks["ablation_runtime_integrity"] = "FAIL"
            anomalies.append(
                f"{variant_runtime_errors} records violated "
                "expected variant component execution rules."
            )
            failed_count += variant_runtime_errors

        # ── 5. Failure Rate Calculation ──────────────────────────────────────
        failure_rate = round(failed_count / max(total_records, 1), 4)

        if (
            checks.get("no_mock_leakage") == "FAIL"
            or checks.get("cryptographic_hashes") == "FAIL"
            or failure_rate > 0.05
        ):
            verdict = "FAIL"
        elif failure_rate > 0.02 or checks.get("response_variability") == "WARN":
            verdict = "WARN"
        else:
            verdict = "PASS"

        return {
            "verdict": verdict,
            "records_audited": total_records,
            "failed_records": failed_count,
            "failure_rate": failure_rate,
            "checks": checks,
            "anomalies": anomalies,
        }
