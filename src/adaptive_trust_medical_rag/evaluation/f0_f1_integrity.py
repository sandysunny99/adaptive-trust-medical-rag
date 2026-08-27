"""F0/F1 Experiment Integrity Auditor

Project: Adaptive Trust-Aware Medical RAG
Component: F0F1IntegrityAuditor

Provides independent, deterministic audit verification of F0 vs F1 evidence contribution
experiment results, ensuring:
  1. Real case-level empirical execution (case_results.jsonl)
  2. Strict paired case design (every case evaluated in both F0 and F1)
  3. Proper evidence backend differentiation (BASE_CORPUS vs BASE_CORPUS_PLUS_P0)
  4. Absence of hard-coded constant deltas or synthetic profile generation
  5. Accurate derivation of aggregate summary metrics directly from case rows
  6. Verifiable P0 snapshot evidence utilization telemetry
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


@dataclass
class F0F1AuditReport:
    """Structured report produced by the F0/F1 Integrity Auditor."""

    verdict: Literal["PASS", "WARN", "FAIL"]
    total_cases: int
    paired_cases: int
    f0_cases_count: int
    f1_cases_count: int
    findings: list[str] = field(default_factory=list)
    metrics_summary: dict[str, Any] = field(default_factory=dict)
    hard_coded_delta_detected: bool = False
    evidence_difference_verified: bool = False
    p0_utilization_verified: bool = False

    def is_valid_research_experiment(self) -> bool:
        return self.verdict in ("PASS", "WARN") and not self.hard_coded_delta_detected


class F0F1IntegrityAuditor:
    """Audits F0/F1 experiment output directories for empirical rigor and integrity."""

    REQUIRED_CASE_FIELDS = [
        "case_id",
        "variant",
        "pipeline_mode",
        "evidence_backend",
        "query_hash",
        "risk_tier",
        "retrieved_document_ids",
        "trust_scores",
        "generated_answer_hash",
        "faithfulness",
        "hallucination_rate",
        "citation_precision",
        "abstained",
        "latency_ms",
    ]

    def audit_run_directory(self, run_dir: Path | str) -> F0F1AuditReport:
        """Execute a full integrity audit on an F0/F1 experiment directory."""
        run_path = Path(run_dir)
        findings: list[str] = []
        verdict: Literal["PASS", "WARN", "FAIL"] = "PASS"

        if not run_path.exists():
            return F0F1AuditReport(
                verdict="FAIL",
                total_cases=0,
                paired_cases=0,
                f0_cases_count=0,
                f1_cases_count=0,
                findings=[f"Run directory not found: {run_path}"],
            )

        jsonl_path = run_path / "case_results.jsonl"
        if not jsonl_path.exists():
            return F0F1AuditReport(
                verdict="FAIL",
                total_cases=0,
                paired_cases=0,
                f0_cases_count=0,
                f1_cases_count=0,
                findings=[f"case_results.jsonl missing in {run_path}"],
            )

        # 1. Parse JSONL case rows
        f0_cases: dict[str, dict[str, Any]] = {}
        f1_cases: dict[str, dict[str, Any]] = {}
        malformed_lines = 0

        with jsonl_path.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except Exception as exc:
                    findings.append(f"Malformed JSON on line {idx}: {exc}")
                    malformed_lines += 1
                    continue

                case_id = record.get("case_id")
                variant = record.get("variant")

                if not case_id or not variant:
                    findings.append(f"Missing case_id or variant on line {idx}")
                    continue

                if variant == "F0":
                    f0_cases[case_id] = record
                elif variant == "F1":
                    f1_cases[case_id] = record
                else:
                    findings.append(f"Unknown variant '{variant}' on line {idx}")

        if malformed_lines > 0:
            verdict = "FAIL"

        # 2. Check Paired Design
        all_case_ids = set(f0_cases.keys()) | set(f1_cases.keys())
        paired_ids = set(f0_cases.keys()) & set(f1_cases.keys())
        f0_only = set(f0_cases.keys()) - set(f1_cases.keys())
        f1_only = set(f1_cases.keys()) - set(f0_cases.keys())

        if f0_only:
            findings.append(f"Cases missing in F1: {sorted(f0_only)[:5]}")
            verdict = "WARN"
        if f1_only:
            findings.append(f"Cases missing in F0: {sorted(f1_only)[:5]}")
            verdict = "WARN"
        if not paired_ids:
            findings.append("Zero paired cases found between F0 and F1")
            verdict = "FAIL"

        # 3. Schema Completeness Check
        for cid, row in {**f0_cases, **f1_cases}.items():
            missing_fields = [f for f in self.REQUIRED_CASE_FIELDS if f not in row]
            if missing_fields:
                findings.append(f"Case {cid} missing fields: {missing_fields}")
                verdict = "FAIL"
                break

        # 4. Evidence Backend Differentiation Check
        evidence_diff_verified = True
        for cid in paired_ids:
            f0_eb = f0_cases[cid].get("evidence_backend", "")
            f1_eb = f1_cases[cid].get("evidence_backend", "")
            if f0_eb == f1_eb and f0_eb != "":
                findings.append(
                    f"Case {cid} has identical evidence_backend in F0 and F1: '{f0_eb}'"
                )
                evidence_diff_verified = False
                verdict = "FAIL"
                break

        # 5. Check for Artificial / Hard-Coded Deltas
        hard_coded_delta = False
        faith_deltas = [
            round(
                f1_cases[cid].get("faithfulness", 0.0)
                - f0_cases[cid].get("faithfulness", 0.0),
                5,
            )
            for cid in paired_ids
        ]
        halluc_deltas = [
            round(
                f1_cases[cid].get("hallucination_rate", 0.0)
                - f0_cases[cid].get("hallucination_rate", 0.0),
                5,
            )
            for cid in paired_ids
        ]

        if len(paired_ids) >= 5:
            # If all cases have an identical non-zero delta across both metrics, flag as simulation
            unique_faith = set(faith_deltas)
            unique_halluc = set(halluc_deltas)
            if len(unique_faith) == 1 and len(unique_halluc) == 1 and 0.0 not in unique_faith:
                val = list(unique_faith)[0]
                findings.append(
                    f"Suspicious constant delta detected across all cases (delta = {val}). "
                    "Indicates hard-coded script arithmetic rather than empirical execution."
                )
                hard_coded_delta = True
                verdict = "FAIL"

        # 6. Verify Summary File & Metric Derivation
        summary_path = run_path / "summary.json"
        metrics_summary: dict[str, Any] = {}
        if summary_path.exists():
            try:
                summary_data = json.loads(summary_path.read_text(encoding="utf-8"))
                metrics_summary = summary_data

                # Validate arithmetic derivation of aggregate means
                f0_faith_calc = sum(r.get("faithfulness", 0.0) for r in f0_cases.values()) / max(
                    len(f0_cases), 1
                )
                f1_faith_calc = sum(r.get("faithfulness", 0.0) for r in f1_cases.values()) / max(
                    len(f1_cases), 1
                )

                f0_faith_rep = summary_data.get("f0", {}).get("faithfulness")
                f1_faith_rep = summary_data.get("f1", {}).get("faithfulness")

                if f0_faith_rep is not None and not math.isclose(
                    f0_faith_calc, f0_faith_rep, abs_tol=1e-3
                ):
                    findings.append(
                        f"Summary F0 faithfulness ({f0_faith_rep}) "
                        f"diverges from JSONL mean ({f0_faith_calc:.4f})"
                    )
                    verdict = "FAIL"

                if f1_faith_rep is not None and not math.isclose(
                    f1_faith_calc, f1_faith_rep, abs_tol=1e-3
                ):
                    findings.append(
                        f"Summary F1 faithfulness ({f1_faith_rep}) "
                        f"diverges from JSONL mean ({f1_faith_calc:.4f})"
                    )
                    verdict = "FAIL"
            except Exception as exc:
                findings.append(f"Failed to parse summary.json: {exc}")
                verdict = "WARN"

        # 7. Verify P0 Utilization in F1
        p0_util_verified = False
        p0_docs_count = sum(len(r.get("p0_document_ids", [])) for r in f1_cases.values())
        p0_retrieved_total = sum(r.get("p0_retrieved_count", 0) for r in f1_cases.values())
        if p0_docs_count > 0 or p0_retrieved_total > 0:
            p0_util_verified = True

        return F0F1AuditReport(
            verdict=verdict,
            total_cases=len(all_case_ids),
            paired_cases=len(paired_ids),
            f0_cases_count=len(f0_cases),
            f1_cases_count=len(f1_cases),
            findings=findings,
            metrics_summary=metrics_summary,
            hard_coded_delta_detected=hard_coded_delta,
            evidence_difference_verified=evidence_diff_verified,
            p0_utilization_verified=p0_util_verified,
        )
