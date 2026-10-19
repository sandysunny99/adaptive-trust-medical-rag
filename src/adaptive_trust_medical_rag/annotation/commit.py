"""Commits researcher-approved annotation decisions to the annotator dataset.

Enforces strict provenance tagging, non-destructive updates, and atomic writes.
Never overwrites previously annotated records.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from adaptive_trust_medical_rag.annotation.schemas import (
    RelevanceLabel,
    ResearcherAction,
    ResearcherDecision,
)

FORBIDDEN_HUMAN_TAGS = {"ANNOTATOR_A", "HUMAN", "HUMAN_EXPERT", "UNASSISTED_HUMAN"}


def commit_researcher_decisions(
    decisions: list[ResearcherDecision],
    annotator_file: Path | str,
    provenance_tag: str = "AI_ASSISTED_RESEARCHER_APPROVED",
) -> dict[str, Any]:
    """Commit researcher-approved decisions back to the annotator file.

    Guarantees:
    - Only commits APPROVE and OVERRIDE decisions (DEFER and REJECT are skipped).
    - Assigns annotator_id to provenance_tag (never misattributed as independent human).
    - Strictly never overwrites existing ANNOTATED records.
    - Performs atomic file replacement to prevent data corruption.

    Args:
        decisions: List of ResearcherDecision instances.
        annotator_file: Path to the target annotator JSONL file.
        provenance_tag: Provenance identifier for the commit.

    Returns:
        Summary dict containing counts of committed and skipped positions.
    """
    target_path = Path(annotator_file).resolve()
    if not target_path.exists():
        raise FileNotFoundError(f"Target annotator file not found: {target_path}")

    # Enforce provenance integrity
    clean_tag = provenance_tag.strip().upper()
    if clean_tag in FORBIDDEN_HUMAN_TAGS or ("HUMAN" in clean_tag and "AI" not in clean_tag):
        raise ValueError(
            f"Invalid provenance tag '{provenance_tag}': AI-assisted annotations must never "
            "be tagged as unassisted human annotations."
        )

    # Index decisions by position_id
    decision_map: dict[str, ResearcherDecision] = {d.position_id: d for d in decisions}

    approved_count = 0
    override_count = 0
    skipped_existing_count = 0
    skipped_deferred_count = 0
    skipped_rejected_count = 0
    committed_position_ids: list[str] = []

    # Read all lines from existing file
    existing_records: list[dict[str, Any]] = []
    with open(target_path, encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if line_str:
                existing_records.append(json.loads(line_str))

    updated_records: list[dict[str, Any]] = []

    for record in existing_records:
        pid = record.get("position_id")
        current_status = record.get("annotation_status", "UNANNOTATED")

        # Guard: NEVER overwrite already ANNOTATED or FROZEN records
        if current_status in ("ANNOTATED", "FROZEN", "QA_RESOLVED"):
            if pid in decision_map:
                skipped_existing_count += 1
            updated_records.append(record)
            continue

        if pid in decision_map:
            decision = decision_map[pid]
            action = decision.researcher_action

            if action == ResearcherAction.APPROVE:
                lbl_val = (
                    decision.final_label.value
                    if isinstance(decision.final_label, RelevanceLabel)
                    else decision.final_label
                )
                record["annotator_id"] = provenance_tag
                record["label"] = lbl_val
                record["relevance_grade"] = decision.final_grade
                record["rationale"] = (
                    decision.researcher_rationale or decision.recommendation.proposed_rationale
                )
                record["evidence_span"] = (
                    decision.final_evidence_span
                    if decision.final_evidence_span is not None
                    else decision.recommendation.best_supporting_span
                )
                record["timestamp"] = decision.decision_timestamp
                record["annotation_status"] = "ANNOTATED"
                record["human_confirmation"] = True
                record["llm_assistance"] = provenance_tag

                approved_count += 1
                committed_position_ids.append(pid)

            elif action == ResearcherAction.OVERRIDE:
                lbl_val = (
                    decision.final_label.value
                    if isinstance(decision.final_label, RelevanceLabel)
                    else decision.final_label
                )
                record["annotator_id"] = provenance_tag
                record["label"] = lbl_val
                record["relevance_grade"] = decision.final_grade
                record["rationale"] = decision.researcher_rationale
                record["evidence_span"] = decision.final_evidence_span or ""
                record["timestamp"] = decision.decision_timestamp
                record["annotation_status"] = "ANNOTATED"
                record["human_confirmation"] = True
                record["llm_assistance"] = f"{provenance_tag}_OVERRIDDEN"

                override_count += 1
                committed_position_ids.append(pid)

            elif action == ResearcherAction.DEFER:
                skipped_deferred_count += 1
                # Preserves status as UNANNOTATED or leaves untouched
            elif action == ResearcherAction.REJECT:
                skipped_rejected_count += 1

        updated_records.append(record)

    # Atomic write to temporary file then replace
    temp_path = target_path.with_suffix(f".tmp_{os.getpid()}")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            for rec in updated_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        # Replace original file atomically
        os.replace(temp_path, target_path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass

    total_committed = approved_count + override_count

    return {
        "total_decisions_evaluated": len(decisions),
        "approved_committed": approved_count,
        "overridden_committed": override_count,
        "total_committed": total_committed,
        "skipped_existing_annotated": skipped_existing_count,
        "skipped_deferred": skipped_deferred_count,
        "skipped_rejected": skipped_rejected_count,
        "provenance_tag": provenance_tag,
        "annotator_file": str(target_path),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "committed_position_ids": committed_position_ids,
    }
