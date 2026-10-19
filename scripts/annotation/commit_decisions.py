#!/usr/bin/env python3
"""Commit researcher-reviewed decisions to the annotator file.

Loads researcher decisions from track_a_annotation/ai_assisted/RESEARCHER_DECISIONS_V1.jsonl,
validates completeness, shows a summary, asks for confirmation, and commits approved/overridden
decisions to the annotator file with AI provenance tags.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.annotation.common import (
    DEFAULT_ANNOTATOR_FILE,
    DEFAULT_COMMIT_AUDIT_JSON,
    DEFAULT_COMMIT_AUDIT_REPORT,
    DEFAULT_DECISIONS_FILE,
    LABEL_TO_GRADE,
    VALID_LABELS,
    load_jsonl,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Commit researcher-reviewed annotation decisions to annotator file.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--decisions-file",
        type=str,
        default=str(DEFAULT_DECISIONS_FILE),
        help="Path to researcher decisions JSONL file.",
    )
    parser.add_argument(
        "--annotator-file",
        type=str,
        default=str(DEFAULT_ANNOTATOR_FILE),
        help="Path to target annotator JSONL file.",
    )
    parser.add_argument(
        "--provenance-tag",
        type=str,
        default="AI_ASSISTED_RESEARCHER_APPROVED",
        help="Provenance identifier for committed annotations.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show summary without committing.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    decisions_path = Path(args.decisions_file)
    annotator_path = Path(args.annotator_file)

    if not decisions_path.is_file():
        print(f"[ERROR] Decisions file not found: {decisions_path}")
        print("Please run review_recommendations.py first.")
        sys.exit(1)

    if not annotator_path.is_file():
        print(f"[ERROR] Annotator file not found: {annotator_path}")
        sys.exit(1)

    # Validate provenance tag
    forbidden_tags = {"ANNOTATOR_A", "HUMAN", "HUMAN_EXPERT", "UNASSISTED_HUMAN"}
    clean_tag = args.provenance_tag.strip().upper()
    if clean_tag in forbidden_tags or ("HUMAN" in clean_tag and "AI" not in clean_tag):
        print(f"[ERROR] Invalid provenance tag '{args.provenance_tag}': "
              "AI-assisted annotations must never be tagged as unassisted human annotations.")
        sys.exit(1)

    # Load decisions
    decisions = load_jsonl(decisions_path)
    if not decisions:
        print("No decisions to commit.")
        sys.exit(0)

    # Classify decisions
    approve_decs = [d for d in decisions if d.get("action") == "APPROVE"]
    override_decs = [d for d in decisions if d.get("action") == "OVERRIDE"]
    defer_decs = [d for d in decisions if d.get("action") == "DEFER"]
    reject_decs = [d for d in decisions if d.get("action") == "REJECT"]
    committable = approve_decs + override_decs

    # Load existing annotator records
    annotator_records = load_jsonl(annotator_path)
    existing_annotated_pids = {
        r["position_id"] for r in annotator_records
        if r.get("annotation_status") in ("ANNOTATED", "FROZEN", "QA_RESOLVED")
    }

    # Filter out already-annotated
    committable_filtered = [
        d for d in committable
        if d.get("position_id") not in existing_annotated_pids
    ]
    skipped_existing = len(committable) - len(committable_filtered)

    # Summary
    print("=" * 70)
    print("  ANNOTATION COMMIT SUMMARY")
    print("=" * 70)
    print(f"  Decisions File        : {decisions_path}")
    print(f"  Target Annotator File : {annotator_path}")
    print(f"  Provenance Tag        : {args.provenance_tag}")
    print(f"  Total Decisions       : {len(decisions)}")
    print(f"  - APPROVE             : {len(approve_decs)}")
    print(f"  - OVERRIDE            : {len(override_decs)}")
    print(f"  - DEFER (skip)        : {len(defer_decs)}")
    print(f"  - REJECT (skip)       : {len(reject_decs)}")
    print(f"  Committable           : {len(committable_filtered)}")
    print(f"  Skipped (existing)    : {skipped_existing}")
    print("=" * 70)

    # Label distribution of committable decisions
    label_counts: dict[str, int] = {}
    for d in committable_filtered:
        lbl = d.get("final_label") or d.get("label") or "UNKNOWN"
        label_counts[lbl] = label_counts.get(lbl, 0) + 1

    print("\n  Label Distribution of Committable:")
    for lbl, cnt in sorted(label_counts.items()):
        print(f"    {lbl}: {cnt}")

    if args.dry_run:
        print("\n[DRY RUN] No changes committed.")
        return

    if not committable_filtered:
        print("\nNo committable decisions after filtering. Nothing to do.")
        return

    # Confirmation
    if not args.yes:
        confirm = input(f"\nCommit {len(committable_filtered)} decisions to {annotator_path}? [y/N]: ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            return

    # Create backup
    backup_path = annotator_path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")
    shutil.copy2(annotator_path, backup_path)
    print(f"Backup created: {backup_path}")

    # Build decision index
    decision_map = {d["position_id"]: d for d in committable_filtered}

    # Apply commits
    updated_records = []
    committed_count = 0
    now_iso = datetime.now(timezone.utc).isoformat()

    for record in annotator_records:
        pid = record.get("position_id")
        current_status = record.get("annotation_status", "UNANNOTATED")

        if current_status in ("ANNOTATED", "FROZEN", "QA_RESOLVED"):
            updated_records.append(record)
            continue

        if pid in decision_map:
            dec = decision_map[pid]
            final_label = dec.get("final_label") or dec.get("label")
            final_grade = dec.get("final_grade") or dec.get("relevance_grade")

            if final_label and final_label in VALID_LABELS:
                record["annotator_id"] = args.provenance_tag
                record["label"] = final_label
                record["relevance_grade"] = final_grade if final_grade is not None else LABEL_TO_GRADE.get(final_label)
                record["rationale"] = dec.get("final_rationale") or dec.get("rationale") or ""
                record["evidence_span"] = dec.get("final_evidence_span") or dec.get("evidence_span") or ""
                record["timestamp"] = dec.get("timestamp") or now_iso
                record["annotation_status"] = "ANNOTATED"
                record["human_confirmation"] = dec.get("human_confirmation", True)
                record["llm_assistance"] = dec.get("provenance", args.provenance_tag)
                committed_count += 1

        updated_records.append(record)

    # Atomic write
    temp_path = annotator_path.with_suffix(f".tmp_{os.getpid()}")
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            for rec in updated_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        os.replace(temp_path, annotator_path)
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass

    # Generate audit report
    audit_summary = {
        "commit_timestamp": now_iso,
        "decisions_file": str(decisions_path),
        "annotator_file": str(annotator_path),
        "backup_file": str(backup_path),
        "provenance_tag": args.provenance_tag,
        "total_decisions": len(decisions),
        "approved": len(approve_decs),
        "overridden": len(override_decs),
        "deferred": len(defer_decs),
        "rejected": len(reject_decs),
        "committed": committed_count,
        "skipped_existing": skipped_existing,
        "label_distribution": label_counts,
    }

    DEFAULT_COMMIT_AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_COMMIT_AUDIT_JSON.write_text(json.dumps(audit_summary, indent=2), encoding="utf-8")

    audit_md = [
        "# Annotation Commit Audit Report",
        f"**Timestamp**: {now_iso}",
        f"**Provenance**: `{args.provenance_tag}`",
        "",
        f"- **Total Decisions Evaluated**: {len(decisions)}",
        f"- **Committed**: {committed_count}",
        f"- **Skipped (existing ANNOTATED)**: {skipped_existing}",
        f"- **Deferred**: {len(defer_decs)}",
        f"- **Rejected**: {len(reject_decs)}",
        f"- **Backup**: `{backup_path.name}`",
        "",
        "## Label Distribution",
        "| Label | Count |",
        "| :--- | :--- |",
    ]
    for lbl, cnt in sorted(label_counts.items()):
        audit_md.append(f"| {lbl} | {cnt} |")

    DEFAULT_COMMIT_AUDIT_REPORT.write_text("\n".join(audit_md), encoding="utf-8")

    print(f"\n✓ Successfully committed {committed_count} annotations.")
    print(f"  Audit Report: {DEFAULT_COMMIT_AUDIT_REPORT}")
    print(f"  Audit JSON  : {DEFAULT_COMMIT_AUDIT_JSON}")


if __name__ == "__main__":
    main()
